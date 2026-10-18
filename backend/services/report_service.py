"""ReportService — зведена статистика для дашборда адміністратора."""
from collections import defaultdict
from datetime import datetime, timedelta

import patterns
from repositories import OrderRepository, ProductRepository, UserRepository, PharmacyRepository

LOW_STOCK_THRESHOLD = 5


class ReportService:
    def __init__(self, orders: OrderRepository, products: ProductRepository,
                 users: UserRepository, pharmacies: PharmacyRepository):
        self.orders, self.products, self.users, self.pharmacies = orders, products, users, pharmacies

    def dashboard(self, days: int = 14) -> dict:
        orders = self.orders.all()
        valid = [o for o in orders if o.status != "cancelled"]
        by_status = defaultdict(int)
        for o in orders:
            by_status[o.status] += 1

        today = datetime.utcnow().date()
        per_day = {(today - timedelta(days=i)): 0.0 for i in range(days - 1, -1, -1)}
        for o in valid:
            day = o.created_at.date()
            if day in per_day:
                per_day[day] += o.total_price

        revenue = sum(o.total_price for o in valid)
        loyalty = defaultdict(int)
        for u in self.users.all():
            loyalty[u.loyalty_type] += 1

        return {
            "totals": {"products": self.products.count(), "pharmacies": len(self.pharmacies.all()),
                       "users": self.users.count(), "orders": len(orders),
                       "revenue": round(revenue, 2),
                       "avg_check": round(revenue / len(valid), 2) if valid else 0,
                       "active_orders": sum(1 for o in orders if not patterns.get_state(o.status).is_final)},
            "orders_by_status": [{"status": s, "label": patterns.get_state(s).label, "count": by_status.get(s, 0)}
                                 for s in patterns.ORDER_STATUSES],
            "revenue_by_day": [{"date": d.strftime("%d.%m"), "revenue": round(v, 2)} for d, v in per_day.items()],
            "top_products": [{"name": n, "quantity": int(q or 0), "revenue": round(float(r or 0), 2)}
                             for n, q, r in self.orders.top_products(5)],
            "low_stock": [{"id": p.id, "name": p.name, "quantity": p.stock_quantity}
                          for p in self.products.low_stock(LOW_STOCK_THRESHOLD)],
            "loyalty": [{"type": t, "label": patterns.get_strategy(t).label, "count": loyalty.get(t, 0)}
                        for t in ("regular", "social", "premium")],
        }
