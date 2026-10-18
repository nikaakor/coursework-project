from datetime import date
from typing import Dict, Iterable, List, Optional

from sqlalchemy import func

import models
from .base import Repository


class ProductRepository(Repository):
    def get(self, product_id: int) -> Optional[models.Product]:
        return self.db.get(models.Product, product_id)

    def get_many(self, ids: Iterable[int]) -> Dict[int, models.Product]:
        ids = list(ids)
        if not ids:
            return {}
        rows = self.db.query(models.Product).filter(models.Product.id.in_(ids)).all()
        return {p.id: p for p in rows}

    def list(self, category: Optional[str] = None, is_prescription: Optional[bool] = None,
             in_stock_only: bool = False) -> List[models.Product]:
        q = self.db.query(models.Product)
        if category and category != "all":
            q = q.filter(models.Product.category == category)
        if is_prescription is not None:
            q = q.filter(models.Product.is_prescription == is_prescription)
        if in_stock_only:
            q = q.filter(models.Product.stock_quantity > 0)
        return q.all()

    def all(self) -> List[models.Product]:
        return self.db.query(models.Product).order_by(models.Product.id).all()

    def count(self) -> int:
        return self.db.query(models.Product).count()

    def low_stock(self, threshold: int) -> List[models.Product]:
        return (self.db.query(models.Product).filter(models.Product.stock_quantity <= threshold)
                .order_by(models.Product.stock_quantity).all())

    def has_orders(self, product_id: int) -> bool:
        return self.db.query(models.OrderItem).filter_by(product_id=product_id).first() is not None

    def purge(self, product: models.Product):
        """Видаляє товар разом із залежними записами (залишки, акції, рецепти, підписки)."""
        for model in (models.PharmacyStock, models.Promotion, models.Prescription, models.Subscription):
            self.db.query(model).filter_by(product_id=product.id).delete()
        self.db.delete(product)

    def sold_counts(self) -> Dict[int, int]:
        rows = (self.db.query(models.OrderItem.product_id, func.sum(models.OrderItem.quantity))
                .group_by(models.OrderItem.product_id).all())
        return {pid: int(total or 0) for pid, total in rows}


class PromotionRepository(Repository):
    def all(self) -> List[models.Promotion]:
        return self.db.query(models.Promotion).order_by(models.Promotion.date_to.desc()).all()

    def get(self, promo_id: int) -> Optional[models.Promotion]:
        return self.db.get(models.Promotion, promo_id)

    def active(self, today: Optional[date] = None) -> List[models.Promotion]:
        today = today or date.today()
        return self.db.query(models.Promotion).filter(
            models.Promotion.date_from <= today, models.Promotion.date_to >= today).all()


class PharmacyRepository(Repository):
    def get(self, pharmacy_id: int) -> Optional[models.Pharmacy]:
        return self.db.get(models.Pharmacy, pharmacy_id)

    def all(self) -> List[models.Pharmacy]:
        return self.db.query(models.Pharmacy).all()

    def stock_row(self, pharmacy_id: int, product_id: int) -> Optional[models.PharmacyStock]:
        return self.db.query(models.PharmacyStock).filter_by(
            pharmacy_id=pharmacy_id, product_id=product_id).first()

    def stock_map(self, product_ids: Iterable[int]) -> Dict[tuple, int]:
        ids = list(product_ids)
        if not ids:
            return {}
        rows = self.db.query(models.PharmacyStock).filter(models.PharmacyStock.product_id.in_(ids)).all()
        return {(r.pharmacy_id, r.product_id): r.quantity for r in rows}

    def set_stock(self, pharmacy_id: int, product_id: int, quantity: int):
        row = self.stock_row(pharmacy_id, product_id)
        if row:
            row.quantity = quantity
        else:
            self.add(models.PharmacyStock(pharmacy_id=pharmacy_id, product_id=product_id, quantity=quantity))

    def stock_of(self, pharmacy_id: int) -> Dict[int, int]:
        rows = self.db.query(models.PharmacyStock).filter_by(pharmacy_id=pharmacy_id).all()
        return {r.product_id: r.quantity for r in rows}

    def totals_by_product(self) -> Dict[int, int]:
        rows = (self.db.query(models.PharmacyStock.product_id, func.sum(models.PharmacyStock.quantity))
                .group_by(models.PharmacyStock.product_id).all())
        return {pid: int(total or 0) for pid, total in rows}

    def has_orders(self, pharmacy_id: int) -> bool:
        return self.db.query(models.Order).filter_by(pharmacy_id=pharmacy_id).first() is not None

    def purge(self, pharmacy: models.Pharmacy):
        self.db.query(models.PharmacyStock).filter_by(pharmacy_id=pharmacy.id).delete()
        self.db.delete(pharmacy)
