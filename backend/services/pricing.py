"""Чисті функції цін/серіалізації (без доступу до БД)."""
import patterns


def promo_rate(product, promos) -> float:
    rates = [p.discount_percent for p in promos
             if p.product_id == product.id
             or (p.product_id is None and p.category in (None, product.category))]
    return max(rates, default=0.0) / 100


def product_out(p, promos) -> dict:
    d = {c.name: getattr(p, c.name) for c in p.__table__.columns}
    rate = promo_rate(p, promos)
    d["promo_percent"] = round(rate * 100, 1)
    d["final_price"] = round(p.price * (1 - rate), 2)
    return d


def user_out(u) -> dict:
    return {"id": u.id, "name": u.name, "email": u.email, "loyalty_type": u.loyalty_type,
            "loyalty_label": patterns.get_strategy(u.loyalty_type).label,
            "bonus_points": round(u.bonus_points or 0, 2)}


def order_out(o) -> dict:
    return {
        "id": o.id, "status": o.status, "status_label": patterns.get_state(o.status).label,
        "delivery_type": o.delivery_type,
        "pharmacy": f"{o.pharmacy.name}, {o.pharmacy.address}" if o.pharmacy else None,
        "address": o.address, "subtotal": o.subtotal, "discount_total": o.discount_total,
        "delivery_fee": o.delivery_fee, "bonus_spent": o.bonus_spent, "bonus_earned": o.bonus_earned,
        "total_price": o.total_price, "created_at": o.created_at.strftime("%d.%m.%Y %H:%M"),
        "items": [{"product_id": i.product_id, "name": i.product_name, "price": i.price,
                   "discount_percent": i.discount_percent, "quantity": i.quantity} for i in o.items],
    }


def summary_out(res: dict) -> dict:
    d = {k: v for k, v in res.items() if k not in ("lines", "pharmacy")}
    d["lines"] = [{"product_id": l["product"].id, "name": l["product"].name, "quantity": l["quantity"],
                   "price": l["product"].price, "discount_percent": round(l["rate"] * 100, 1)}
                  for l in res["lines"]]
    return d
