from typing import Literal, Optional
from fastapi import APIRouter, Depends

from deps import get_catalog_service
from services import CatalogService

router = APIRouter(tags=["Каталог"])


@router.get("/products/")
def get_products(category: Optional[str] = None, search: Optional[str] = None,
                 is_prescription: Optional[bool] = None, in_stock_only: bool = False,
                 min_price: Optional[float] = None, max_price: Optional[float] = None,
                 sort: Literal["popular", "asc", "desc"] = "popular",
                 service: CatalogService = Depends(get_catalog_service)):
    return service.search(category, search, is_prescription, in_stock_only, min_price, max_price, sort)


@router.get("/products/{product_id}")
def get_product_detail(product_id: int, service: CatalogService = Depends(get_catalog_service)):
    return service.get(product_id)


@router.get("/promotions/")
def list_promotions(service: CatalogService = Depends(get_catalog_service)):
    return service.active_promotions()
