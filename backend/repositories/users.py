from datetime import date
from typing import List, Optional

from sqlalchemy import func

import models
from .base import Repository


class UserRepository(Repository):
    def get(self, user_id: int) -> Optional[models.User]:
        return self.db.get(models.User, user_id)

    def all(self) -> List[models.User]:
        return self.db.query(models.User).order_by(models.User.id).all()

    def count(self) -> int:
        return self.db.query(models.User).count()

    def get_by_email(self, email: str) -> Optional[models.User]:
        return self.db.query(models.User).filter(func.lower(models.User.email) == email.strip().lower()).first()


class PrescriptionRepository(Repository):
    def find_valid(self, user_id: int, product_id: int, today: date) -> Optional[models.Prescription]:
        return (self.db.query(models.Prescription)
                .filter(models.Prescription.user_id == user_id, models.Prescription.product_id == product_id,
                        models.Prescription.is_used == False,  # noqa: E712
                        models.Prescription.valid_until >= today)
                .order_by(models.Prescription.valid_until).first())

    def for_user(self, user_id: int) -> List[models.Prescription]:
        return (self.db.query(models.Prescription).filter(models.Prescription.user_id == user_id)
                .order_by(models.Prescription.valid_until.desc()).all())


class SubscriptionRepository(Repository):
    def for_user(self, user_id: int) -> List[models.Subscription]:
        return self.db.query(models.Subscription).filter(models.Subscription.user_id == user_id).all()

    def find(self, user_id: int, product_id: int, kind: str) -> Optional[models.Subscription]:
        return self.db.query(models.Subscription).filter_by(
            user_id=user_id, product_id=product_id, kind=kind).first()

    def get(self, sub_id: int, user_id: int) -> Optional[models.Subscription]:
        return self.db.query(models.Subscription).filter_by(id=sub_id, user_id=user_id).first()

    def regular_for(self, user_id: int, product_ids) -> List[models.Subscription]:
        return self.db.query(models.Subscription).filter(
            models.Subscription.user_id == user_id, models.Subscription.kind == "regular",
            models.Subscription.product_id.in_(list(product_ids))).all()


class NotificationRepository(Repository):
    def recent(self, user_id: int, limit: int = 20) -> List[models.Notification]:
        return (self.db.query(models.Notification).filter(models.Notification.user_id == user_id)
                .order_by(models.Notification.id.desc()).limit(limit).all())
