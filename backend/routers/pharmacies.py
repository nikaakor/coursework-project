from typing import Optional
from fastapi import APIRouter, Depends

import config
from deps import get_pharmacy_service
from exceptions import DomainError
from services import PharmacyService

router = APIRouter(prefix="/pharmacies", tags=["Аптеки"])


def parse_items(raw: Optional[str]) -> dict:
    result = {}
    for part in (raw or "").split(","):
        if not part.strip():
            continue
        try:
            pid, qty = part.split(":")
            result[int(pid)] = max(1, int(qty))
        except ValueError:
            raise DomainError("Невірний формат items, очікується 'id:кількість,id:кількість'")
    return result


@router.get("/nearest")
def nearest_pharmacies(lat: float = config.DEFAULT_LAT, lon: float = config.DEFAULT_LON,
                       items: Optional[str] = None, service: PharmacyService = Depends(get_pharmacy_service)):
    """Аптеки за відстанню. Якщо передано items='id:к-сть,...', для кожної показано, чи є все в наявності."""
    return service.nearest(lat, lon, parse_items(items))
