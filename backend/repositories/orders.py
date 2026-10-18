from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func

import models
from .base import Repository


class OrderRepository(Repository):
    def for_user(self, user_id: int) -> List[models.Order]:
        return (self.db.query(models.Order).filter(models.Order.user_id == user_id)
                .order_by(models.Order.id.desc()).all())

    def get(self, order_id: int) -> Optional[models.Order]:
        return self.db.get(models.Order, order_id)

    def all(self, status: Optional[str] = None) -> List[models.Order]:
        q = self.db.query(models.Order)
        if status:
            q = q.filter(models.Order.status == status)
        return q.order_by(models.Order.id.desc()).all()

    def counts_by_user(self) -> dict:
        rows = (self.db.query(models.Order.user_id, func.count(models.Order.id), func.sum(models.Order.total_price))
                .filter(models.Order.status != "cancelled").group_by(models.Order.user_id).all())
        return {uid: (cnt, float(total or 0)) for uid, cnt, total in rows}

    def top_products(self, limit: int = 5) -> List[Tuple[str, int, float]]:
        """Найпопулярніші товари серед не скасованих замовлень: (назва, к-сть, виручка)."""
        qty = func.sum(models.OrderItem.quantity)
        revenue = func.sum(models.OrderItem.quantity * models.OrderItem.price * (1 - models.OrderItem.discount_percent / 100))
        return (self.db.query(models.OrderItem.product_name, qty, revenue)
                .join(models.Order, models.Order.id == models.OrderItem.order_id)
                .filter(models.Order.status != "cancelled")
                .group_by(models.OrderItem.product_name).order_by(qty.desc()).limit(limit).all())

    def created_since(self, since: datetime) -> List[models.Order]:
        return self.db.query(models.Order).filter(models.Order.created_at >= since).all()
