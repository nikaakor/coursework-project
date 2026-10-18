from datetime import date, timedelta

from repositories import SubscriptionRepository, NotificationRepository, PromotionRepository
from .pharmacy_service import PharmacyService
from .user_service import UserService


class NotificationService:
    """Динамічні сповіщення: нагадування, наявність у найближчій аптеці, акції + збережені події замовлень."""

    def __init__(self, users: UserService, subscriptions: SubscriptionRepository,
                 notifications: NotificationRepository, promotions: PromotionRepository,
                 pharmacies: PharmacyService):
        self.users, self.subscriptions = users, subscriptions
        self.notifications, self.promotions, self.pharmacies = notifications, promotions, pharmacies

    def build(self, user_id: int, lat: float, lon: float):
        self.users.require(user_id)
        today = date.today()
        items = []

        for s in self.subscriptions.for_user(user_id):
            if s.kind == "regular":
                last = s.last_order_date or today
                if last + timedelta(days=s.interval_days or 30) <= today:
                    items.append({"type": "reminder", "product_id": s.product_id,
                                  "message": f"Час поповнити запас: «{s.product.name}». "
                                             f"Останнє замовлення — {last:%d.%m.%Y}."})
            elif s.kind == "watch":
                found = self.pharmacies.nearest_with_stock(s.product_id, lat, lon)
                if found:
                    ph, km, qty = found
                    items.append({"type": "availability", "product_id": s.product_id,
                                  "message": f"«{s.product.name}» є в найближчій аптеці: {ph.name}, "
                                             f"{ph.address} ({km:.1f} км, {qty} шт.)."})

        for p in self.promotions.active():
            items.append({"type": "promo", "product_id": p.product_id,
                          "message": f"{p.title}: {p.description} (до {p.date_to:%d.%m.%Y})"})

        for n in self.notifications.recent(user_id):
            items.append({"type": n.kind, "message": n.message,
                          "created_at": n.created_at.strftime("%d.%m.%Y %H:%M")})
        return {"count": len(items), "items": items}
