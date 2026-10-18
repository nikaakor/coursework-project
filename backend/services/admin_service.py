"""AdminService — керування довідниками: товари, аптеки та їх залишки, акції, клієнти."""
import models
from repositories import (ProductRepository, PharmacyRepository, PromotionRepository, UserRepository,
                          OrderRepository)
from exceptions import DomainError, NotFoundError
from .pricing import product_out, user_out

CATEGORIES = ("Ліки", "Вітаміни", "Медичні вироби")


class AdminService:
    def __init__(self, products: ProductRepository, pharmacies: PharmacyRepository,
                 promotions: PromotionRepository, users: UserRepository, orders: OrderRepository = None):
        self.products, self.pharmacies, self.promotions, self.users = products, pharmacies, promotions, users
        self.orders = orders

    def list_products(self) -> list:
        promos = self.promotions.active()
        in_pharmacies = self.pharmacies.totals_by_product()
        sold = self.products.sold_counts()
        out = []
        for p in self.products.all():
            d = product_out(p, promos)
            d["pharmacy_stock_total"] = in_pharmacies.get(p.id, 0)
            d["sold"] = sold.get(p.id, 0)
            out.append(d)
        return out

    def add_product(self, data) -> dict:
        values = data.model_dump()
        values["image_url"] = values["image_url"] or ""
        product = self.products.add(models.Product(**values))
        self.products.commit()
        self.products.refresh(product)
        return {"message": "Товар додано успішно!", "product": product_out(product, self.promotions.active())}

    def update_product(self, product_id: int, data) -> dict:
        product = self._product(product_id)
        for key, value in data.model_dump().items():
            setattr(product, key, value if value is not None else "")
        self.products.commit()
        self.products.refresh(product)
        return {"message": "Товар оновлено", "product": product_out(product, self.promotions.active())}

    def delete_product(self, product_id: int) -> dict:
        product = self._product(product_id)
        if self.products.has_orders(product_id):
            raise DomainError("Товар є в історії замовлень, тому його не можна видалити. "
                              "Встановіть залишок 0 — він зникне з наявності.")
        self.products.purge(product)
        self.products.commit()
        return {"message": "Товар видалено"}

    def list_pharmacies(self) -> list:
        return [{"id": p.id, "name": p.name, "address": p.address, "lat": p.lat, "lon": p.lon,
                 "stock_total": sum(self.pharmacies.stock_of(p.id).values())} for p in self.pharmacies.all()]

    def add_pharmacy(self, data) -> dict:
        ph = self.pharmacies.add(models.Pharmacy(**data.model_dump()))
        self.pharmacies.commit()
        self.pharmacies.refresh(ph)
        return {"message": "Аптеку додано", "id": ph.id}

    def update_pharmacy(self, pharmacy_id: int, data) -> dict:
        ph = self._pharmacy(pharmacy_id)
        for key, value in data.model_dump().items():
            setattr(ph, key, value)
        self.pharmacies.commit()
        return {"message": "Аптеку оновлено"}

    def delete_pharmacy(self, pharmacy_id: int) -> dict:
        ph = self._pharmacy(pharmacy_id)
        if self.pharmacies.has_orders(pharmacy_id):
            raise DomainError("З цією аптекою пов'язані замовлення — видалення неможливе")
        self.pharmacies.purge(ph)
        self.pharmacies.commit()
        return {"message": "Аптеку видалено"}

    def pharmacy_stock(self, pharmacy_id: int) -> list:
        self._pharmacy(pharmacy_id)
        stock = self.pharmacies.stock_of(pharmacy_id)
        return [{"product_id": p.id, "name": p.name, "category": p.category, "quantity": stock.get(p.id, 0)}
                for p in self.products.all()]

    def set_pharmacy_stock(self, pharmacy_id: int, data) -> dict:
        if not self.pharmacies.get(pharmacy_id) or not self.products.get(data.product_id):
            raise NotFoundError("Аптеку або товар не знайдено")
        self.pharmacies.set_stock(pharmacy_id, data.product_id, data.quantity)
        self.pharmacies.commit()
        return {"message": "Залишок оновлено"}

    def list_promotions(self) -> list:
        from datetime import date
        today, names = date.today(), {p.id: p.name for p in self.products.all()}
        return [{"id": p.id, "title": p.title, "description": p.description,
                 "discount_percent": p.discount_percent, "category": p.category,
                 "product_id": p.product_id, "product_name": names.get(p.product_id),
                 "date_from": p.date_from.isoformat(), "date_to": p.date_to.isoformat(),
                 "is_active": p.date_from <= today <= p.date_to} for p in self.promotions.all()]

    def add_promotion(self, data) -> dict:
        if data.date_to < data.date_from:
            raise DomainError("Дата завершення раніше за дату початку")
        if data.category and data.category not in CATEGORIES:
            raise DomainError("Невідома категорія")
        if data.product_id and not self.products.get(data.product_id):
            raise NotFoundError("Товар для акції не знайдено")
        self.promotions.add(models.Promotion(**data.model_dump()))
        self.promotions.commit()
        return {"message": "Акцію створено"}

    def delete_promotion(self, promo_id: int) -> dict:
        promo = self.promotions.get(promo_id)
        if not promo:
            raise NotFoundError("Акцію не знайдено")
        self.promotions.delete(promo)
        self.promotions.commit()
        return {"message": "Акцію видалено"}

    def list_users(self) -> list:
        stats = self.orders.counts_by_user() if self.orders else {}
        out = []
        for u in self.users.all():
            cnt, total = stats.get(u.id, (0, 0.0))
            out.append({**user_out(u), "orders_count": cnt, "orders_total": round(total, 2)})
        return out

    def set_loyalty(self, user_id: int, loyalty_type: str) -> dict:
        user = self._user(user_id)
        user.loyalty_type = loyalty_type
        self.users.commit()
        return user_out(user)

    def adjust_bonus(self, user_id: int, delta: float) -> dict:
        user = self._user(user_id)
        new_value = round((user.bonus_points or 0) + delta, 2)
        if new_value < 0:
            raise DomainError("Баланс бонусів не може бути від'ємним")
        user.bonus_points = new_value
        self.users.commit()
        return user_out(user)

    def _product(self, product_id):
        obj = self.products.get(product_id)
        if not obj:
            raise NotFoundError("Товар не знайдено")
        return obj

    def _pharmacy(self, pharmacy_id):
        obj = self.pharmacies.get(pharmacy_id)
        if not obj:
            raise NotFoundError("Аптеку не знайдено")
        return obj

    def _user(self, user_id):
        obj = self.users.get(user_id)
        if not obj:
            raise NotFoundError("Користувача не знайдено")
        return obj
