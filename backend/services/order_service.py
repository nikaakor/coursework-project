"""OrderService — шаблон Facade: єдиний вхід для сценарію «розрахувати / оформити замовлення».
Всередині координує Factory (get_strategy), Builder (OrderBuilder), Observer (OrderSubject)
та репозиторії."""
from datetime import date

import models
import patterns
from repositories import (UserRepository, ProductRepository, PharmacyRepository, PromotionRepository,
                          PrescriptionRepository, SubscriptionRepository, OrderRepository,
                          NotificationRepository)
from exceptions import DomainError, NotFoundError
from schemas import OrderRequest
from .pricing import promo_rate, order_out, summary_out, user_out


class OrderService:
    def __init__(self, users: UserRepository, products: ProductRepository, pharmacies: PharmacyRepository,
                 promotions: PromotionRepository, prescriptions: PrescriptionRepository,
                 subscriptions: SubscriptionRepository, orders: OrderRepository,
                 notifications: NotificationRepository):
        self.users, self.products, self.pharmacies = users, products, pharmacies
        self.promotions, self.prescriptions, self.subscriptions = promotions, prescriptions, subscriptions
        self.orders, self.notifications = orders, notifications

    def preview(self, req: OrderRequest) -> dict:
        user = self._user(req.user_id)
        res, _, _ = self._prepare(user, req, strict=False)
        return summary_out(res)

    def place(self, req: OrderRequest) -> dict:
        user = self._user(req.user_id)
        res, prescriptions, stock_updates = self._prepare(user, req, strict=True)

        pharmacy = res["pharmacy"]
        order = models.Order(
            user_id=user.id, pharmacy_id=pharmacy.id if pharmacy else None,
            address="" if pharmacy else res["address"], delivery_type=req.delivery_type,
            subtotal=res["subtotal"], discount_total=res["discount_total"], delivery_fee=res["delivery_fee"],
            bonus_spent=res["bonus_spent"], bonus_earned=res["bonus_earned"], total_price=res["total_price"],
            status="reserved" if pharmacy else "new")
        for l in res["lines"]:
            order.items.append(models.OrderItem(
                product_id=l["product"].id, product_name=l["product"].name, price=l["product"].price,
                discount_percent=round(l["rate"] * 100, 1), quantity=l["quantity"]))
        self.orders.add(order)

        for target, qty in stock_updates:
            if isinstance(target, models.Product):
                target.stock_quantity -= qty
            else:
                target.quantity -= qty
        for rx in prescriptions:
            rx.is_used = True
        user.bonus_points = round((user.bonus_points or 0) - res["bonus_spent"] + res["bonus_earned"], 2)

        for sub in self.subscriptions.regular_for(user.id, [l["product"].id for l in res["lines"]]):
            sub.last_order_date = date.today()

        self.orders.flush() 
        where = (f"заброньовано в аптеці {pharmacy.name} ({pharmacy.address})" if pharmacy
                 else "передано в кур'єрську доставку")
        subject = patterns.OrderSubject()
        subject.attach(patterns.DbNotifier(self.notifications, user.id))
        subject.attach(patterns.EmailNotifier())
        subject.attach(patterns.SmsNotifier())
        subject.notify(f"Замовлення №{order.id} на {order.total_price:.2f} грн {where}. "
                       f"Нараховано бонусів: {order.bonus_earned:.2f}.")

        self.orders.commit() 
        self.orders.refresh(order)
        self.users.refresh(user)
        return {"message": "Замовлення оформлено", "order": order_out(order), "user": user_out(user)}

    def history(self, user_id: int) -> list:
        self._user(user_id)
        return [order_out(o) for o in self.orders.for_user(user_id)]

    def _user(self, user_id: int) -> models.User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("Користувача не знайдено")
        return user

    def _prepare(self, user, req: OrderRequest, strict: bool):
        """strict=True — з перевіркою складу, рецептів, аптеки/адреси (оформлення);
           strict=False — лише розрахунок цін (попередній перегляд у кошику)."""
        if not req.items:
            raise DomainError("Кошик порожній")

        merged = {}
        for it in req.items:
            merged[it.product_id] = merged.get(it.product_id, 0) + it.quantity

        pharmacy = None
        if strict:
            if req.delivery_type == "pickup":
                if not req.pharmacy_id:
                    raise DomainError("Оберіть аптеку для самовивозу")
                pharmacy = self.pharmacies.get(req.pharmacy_id)
                if not pharmacy:
                    raise NotFoundError("Аптеку не знайдено")
            elif not (req.address or "").strip():
                raise DomainError("Вкажіть адресу доставки")

        promos = self.promotions.active()
        builder = (patterns.OrderBuilder().set_user(user)
                   .set_delivery(req.delivery_type, pharmacy, (req.address or "").strip())
                   .use_bonuses(req.use_bonuses))
        prescriptions, stock_updates = [], []
        today = date.today()

        for pid, qty in merged.items():
            product = self.products.get(pid)
            if not product:
                raise NotFoundError(f"Товар #{pid} не знайдено")
            if strict:
                if product.is_prescription:
                    rx = self.prescriptions.find_valid(user.id, pid, today)
                    if not rx:
                        raise DomainError(f"Для «{product.name}» потрібен чинний рецепт у вашому кабінеті")
                    prescriptions.append(rx)
                if pharmacy:
                    target = self.pharmacies.stock_row(pharmacy.id, pid)
                    available = target.quantity if target else 0
                else:
                    target, available = product, product.stock_quantity
                if available < qty:
                    where = f"в аптеці {pharmacy.name}" if pharmacy else "на складі"
                    raise DomainError(f"Недостатньо «{product.name}» {where} (є {available})")
                stock_updates.append((target, qty))
            rate = max(builder.strategy.discount_rate(product), promo_rate(product, promos))
            builder.add_item(product, qty, rate)

        return builder.get_result(), prescriptions, stock_updates
