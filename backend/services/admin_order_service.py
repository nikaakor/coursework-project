"""AdminOrderService — керування замовленнями. Переходи між статусами визначає шаблон State,
про кожну зміну клієнта сповіщає Observer (БД + email + sms)."""
import models
import patterns
from repositories import (OrderRepository, UserRepository, ProductRepository, PharmacyRepository,
                          NotificationRepository)
from exceptions import DomainError, NotFoundError
from .pricing import order_out


class AdminOrderService:
    def __init__(self, orders: OrderRepository, users: UserRepository, products: ProductRepository,
                 pharmacies: PharmacyRepository, notifications: NotificationRepository):
        self.orders, self.users, self.products = orders, users, products
        self.pharmacies, self.notifications = pharmacies, notifications

    def list(self, status=None) -> list:
        users = {u.id: u for u in self.users.all()}
        out = []
        for o in self.orders.all(status):
            u = users.get(o.user_id)
            d = order_out(o)
            d["user_name"], d["user_email"] = (u.name, u.email) if u else ("—", "")
            d["next_statuses"] = [{"status": s, "label": patterns.get_state(s).label}
                                  for s in patterns.get_state(o.status).next_states]
            out.append(d)
        return out

    def change_status(self, order_id: int, target: str) -> dict:
        order = self.orders.get(order_id)
        if not order:
            raise NotFoundError("Замовлення не знайдено")
        current, new_state = patterns.get_state(order.status), patterns.get_state(target)
        if not current.can_move_to(target):
            raise DomainError(f"Неможливо перевести замовлення зі статусу «{current.label}» "
                              f"у «{new_state.label}»")

        if target == "cancelled":
            self._rollback(order)
        order.status = target

        user = self.users.get(order.user_id)
        if user and new_state.notify_text:
            subject = patterns.OrderSubject()
            subject.attach(patterns.DbNotifier(self.notifications, user.id))
            subject.attach(patterns.EmailNotifier())
            subject.attach(patterns.SmsNotifier())
            subject.notify(f"Замовлення №{order.id}: {new_state.notify_text}.")
        self.orders.commit()
        self.orders.refresh(order)
        return {"message": f"Статус змінено на «{new_state.label}»", "order": order_out(order)}

    def _rollback(self, order):
        """Скасування: повертаємо товар на склад/в аптеку та виправляємо бонуси клієнта."""
        for item in order.items:
            if order.pharmacy_id:
                row = self.pharmacies.stock_row(order.pharmacy_id, item.product_id)
                if row:
                    row.quantity += item.quantity
                else:
                    self.pharmacies.set_stock(order.pharmacy_id, item.product_id, item.quantity)
            else:
                product = self.products.get(item.product_id)
                if product:
                    product.stock_quantity += item.quantity
        user = self.users.get(order.user_id)
        if user:
            user.bonus_points = max(0.0, round((user.bonus_points or 0) + order.bonus_spent - order.bonus_earned, 2))
