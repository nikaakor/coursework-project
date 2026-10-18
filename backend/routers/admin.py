from typing import Optional
from fastapi import APIRouter, Depends

from deps import get_admin_service, get_admin_order_service, get_report_service, require_admin
from schemas import (ProductCreateRequest, StockUpdate, PromotionCreate, LoyaltyUpdate, PharmacyCreate,
                     OrderStatusUpdate, BonusAdjust)
from services import AdminService, AdminOrderService, ReportService

router = APIRouter(prefix="/admin", tags=["Адмін"], dependencies=[Depends(require_admin)])


@router.get("/stats")
def dashboard(service: ReportService = Depends(get_report_service)):
    return service.dashboard()


@router.get("/products/")
def list_products(service: AdminService = Depends(get_admin_service)):
    return service.list_products()


@router.post("/products/")
def add_product(prod: ProductCreateRequest, service: AdminService = Depends(get_admin_service)):
    return service.add_product(prod)


@router.put("/products/{product_id}")
def update_product(product_id: int, prod: ProductCreateRequest, service: AdminService = Depends(get_admin_service)):
    return service.update_product(product_id, prod)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, service: AdminService = Depends(get_admin_service)):
    return service.delete_product(product_id)


@router.get("/pharmacies/")
def list_pharmacies(service: AdminService = Depends(get_admin_service)):
    return service.list_pharmacies()


@router.post("/pharmacies/")
def add_pharmacy(data: PharmacyCreate, service: AdminService = Depends(get_admin_service)):
    return service.add_pharmacy(data)


@router.put("/pharmacies/{pharmacy_id}")
def update_pharmacy(pharmacy_id: int, data: PharmacyCreate, service: AdminService = Depends(get_admin_service)):
    return service.update_pharmacy(pharmacy_id, data)


@router.delete("/pharmacies/{pharmacy_id}")
def delete_pharmacy(pharmacy_id: int, service: AdminService = Depends(get_admin_service)):
    return service.delete_pharmacy(pharmacy_id)


@router.get("/pharmacies/{pharmacy_id}/stock")
def get_pharmacy_stock(pharmacy_id: int, service: AdminService = Depends(get_admin_service)):
    return service.pharmacy_stock(pharmacy_id)


@router.put("/pharmacies/{pharmacy_id}/stock")
def set_pharmacy_stock(pharmacy_id: int, data: StockUpdate, service: AdminService = Depends(get_admin_service)):
    return service.set_pharmacy_stock(pharmacy_id, data)


@router.get("/promotions/")
def list_promotions(service: AdminService = Depends(get_admin_service)):
    return service.list_promotions()


@router.post("/promotions/")
def add_promotion(data: PromotionCreate, service: AdminService = Depends(get_admin_service)):
    return service.add_promotion(data)


@router.delete("/promotions/{promo_id}")
def delete_promotion(promo_id: int, service: AdminService = Depends(get_admin_service)):
    return service.delete_promotion(promo_id)


@router.get("/users/")
def list_users(service: AdminService = Depends(get_admin_service)):
    return service.list_users()


@router.put("/users/{user_id}/loyalty")
def set_loyalty(user_id: int, data: LoyaltyUpdate, service: AdminService = Depends(get_admin_service)):
    return service.set_loyalty(user_id, data.loyalty_type)


@router.post("/users/{user_id}/bonus")
def adjust_bonus(user_id: int, data: BonusAdjust, service: AdminService = Depends(get_admin_service)):
    return service.adjust_bonus(user_id, data.delta)


@router.get("/orders/")
def list_orders(status: Optional[str] = None, service: AdminOrderService = Depends(get_admin_order_service)):
    return service.list(status)


@router.put("/orders/{order_id}/status")
def change_order_status(order_id: int, data: OrderStatusUpdate,
                        service: AdminOrderService = Depends(get_admin_order_service)):
    return service.change_status(order_id, data.status)
