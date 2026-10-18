from math import radians, sin, cos, asin, sqrt
from typing import Dict, Optional

from repositories import PharmacyRepository, ProductRepository
from exceptions import NotFoundError


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


class PharmacyService:
    def __init__(self, pharmacies: PharmacyRepository, products: ProductRepository):
        self.pharmacies, self.products = pharmacies, products

    def by_distance(self, lat: float, lon: float):
        return sorted(((p, haversine_km(lat, lon, p.lat, p.lon)) for p in self.pharmacies.all()),
                      key=lambda x: x[1])

    def nearest(self, lat: float, lon: float, need: Optional[Dict[int, int]] = None):
        """Аптеки за відстанню; для кожної — чи є в наявності все з need ({product_id: кількість})."""
        need = need or {}
        stocks = self.pharmacies.stock_map(need.keys())
        names = {pid: p.name for pid, p in self.products.get_many(need.keys()).items()}
        out = []
        for ph, km in self.by_distance(lat, lon):
            missing = [names.get(pid, str(pid)) for pid, qty in need.items() if stocks.get((ph.id, pid), 0) < qty]
            out.append({"id": ph.id, "name": ph.name, "address": ph.address, "distance_km": round(km, 2),
                        "has_all": not missing, "missing": missing})
        return out

    def nearest_with_stock(self, product_id: int, lat: float, lon: float):
        """Найближча аптека, де товар є: (аптека, км, к-сть) або None."""
        stocks = self.pharmacies.stock_map([product_id])
        for ph, km in self.by_distance(lat, lon):
            qty = stocks.get((ph.id, product_id), 0)
            if qty > 0:
                return ph, km, qty
        return None
