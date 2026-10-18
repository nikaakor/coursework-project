from datetime import date

import models
from repositories import UserRepository, ProductRepository, PrescriptionRepository, SubscriptionRepository
from exceptions import DomainError, NotFoundError
from .pricing import user_out


class UserService:
    def __init__(self, users: UserRepository, products: ProductRepository,
                 prescriptions: PrescriptionRepository, subscriptions: SubscriptionRepository):
        self.users, self.products = users, products
        self.prescriptions, self.subscriptions = prescriptions, subscriptions

    def require(self, user_id: int) -> models.User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("Користувача не знайдено")
        return user

    def get(self, user_id: int):
        return user_out(self.require(user_id))

    def register(self, name: str, email: str):
        email = email.strip().lower()
        if self.users.get_by_email(email):
            raise DomainError("Користувач з таким Email вже існує!")
        user = self.users.add(models.User(name=name.strip(), email=email, loyalty_type="regular", bonus_points=50.0))
        self.users.commit()
        self.users.refresh(user)
        return {"message": "Реєстрацію завершено! Нараховано 50 вітальних бонусів.", "user": user_out(user)}

    def login(self, email: str):
        user = self.users.get_by_email(email)
        if not user:
            raise NotFoundError("Користувача з таким Email не знайдено!")
        return {"message": "Вхід успішний!", "user": user_out(user)}

    def list_prescriptions(self, user_id: int):
        self.require(user_id)
        today = date.today()
        return [{"id": r.id, "code": r.code, "product_id": r.product_id, "drug_name": r.product.name,
                 "doctor": r.doctor, "valid_until": r.valid_until.strftime("%d.%m.%Y"),
                 "is_used": r.is_used, "is_valid": (not r.is_used) and r.valid_until >= today}
                for r in self.prescriptions.for_user(user_id)]

    def add_prescription(self, user_id: int, data):
        self.require(user_id)
        if not self.products.get(data.product_id):
            raise NotFoundError("Препарат не знайдено")
        if data.valid_until < date.today():
            raise DomainError("Рецепт уже прострочений")
        self.prescriptions.add(models.Prescription(user_id=user_id, **data.model_dump()))
        self.prescriptions.commit()
        return {"message": "Рецепт збережено"}

    def list_subscriptions(self, user_id: int):
        self.require(user_id)
        return [{"id": s.id, "kind": s.kind, "product_id": s.product_id, "product_name": s.product.name,
                 "interval_days": s.interval_days} for s in self.subscriptions.for_user(user_id)]

    def add_subscription(self, user_id: int, data):
        self.require(user_id)
        if not self.products.get(data.product_id):
            raise NotFoundError("Товар не знайдено")
        if data.kind == "regular" and not data.interval_days:
            raise DomainError("Вкажіть інтервал нагадування в днях")
        sub = self.subscriptions.find(user_id, data.product_id, data.kind)
        if sub:
            sub.interval_days = data.interval_days
        else:
            self.subscriptions.add(models.Subscription(
                user_id=user_id, product_id=data.product_id, kind=data.kind,
                interval_days=data.interval_days, last_order_date=date.today()))
        self.subscriptions.commit()
        return {"message": "Нагадування збережено" if data.kind == "regular" else "Повідомимо, коли товар з'явиться"}

    def delete_subscription(self, user_id: int, sub_id: int):
        sub = self.subscriptions.get(sub_id, user_id)
        if not sub:
            raise NotFoundError("Підписку не знайдено")
        self.subscriptions.delete(sub)
        self.subscriptions.commit()
        return {"message": "Видалено"}
