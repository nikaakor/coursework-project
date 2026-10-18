from fastapi import APIRouter, Depends

from deps import get_order_service
from schemas import OrderRequest
from services import OrderService

router = APIRouter(prefix="/orders", tags=["Замовлення"])


@router.post("/preview")
def preview_order(req: OrderRequest, service: OrderService = Depends(get_order_service)):
    return service.preview(req)


@router.post("/create-full")
def create_full_order(req: OrderRequest, service: OrderService = Depends(get_order_service)):
    return service.place(req)


@router.get("/user/{user_id}")
def get_user_orders(user_id: int, service: OrderService = Depends(get_order_service)):
    return service.history(user_id)
