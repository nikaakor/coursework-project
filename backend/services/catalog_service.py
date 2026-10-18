from typing import Optional

from repositories import ProductRepository, PromotionRepository
from exceptions import NotFoundError
from .pricing import product_out


class CatalogService:
    def __init__(self, products: ProductRepository, promotions: PromotionRepository):
        self.products, self.promotions = products, promotions

    def search(self, category=None, search=None, is_prescription=None, in_stock_only=False,
               min_price: Optional[float] = None, max_price: Optional[float] = None, sort="popular"):
        items = self.products.list(category, is_prescription, in_stock_only)

        if search and search.strip():
            s = search.strip().casefold()
            items = [p for p in items if any(
                s in (v or "").casefold() for v in (p.name, p.manufacturer, p.category, p.active_ingredient))]

        promos = self.promotions.active()
        result = [product_out(p, promos) for p in items]
        if min_price is not None:
            result = [p for p in result if p["final_price"] >= min_price]
        if max_price is not None:
            result = [p for p in result if p["final_price"] <= max_price]

        if sort == "asc":
            result.sort(key=lambda p: p["final_price"])
        elif sort == "desc":
            result.sort(key=lambda p: -p["final_price"])
        else:
            sold = self.products.sold_counts()
            result.sort(key=lambda p: (-sold.get(p["id"], 0), p["id"]))
        return result

    def get(self, product_id: int):
        product = self.products.get(product_id)
        if not product:
            raise NotFoundError("Товар не знайдено")
        return product_out(product, self.promotions.active())

    def active_promotions(self):
        return [{"id": p.id, "title": p.title, "description": p.description,
                 "discount_percent": p.discount_percent, "category": p.category,
                 "product_id": p.product_id, "date_to": p.date_to.strftime("%d.%m.%Y")}
                for p in self.promotions.active()]
