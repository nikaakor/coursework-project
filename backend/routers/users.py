import config
from fastapi import APIRouter, Depends

from deps import get_user_service, get_notification_service
from schemas import UserRegister, UserLogin, PrescriptionCreate, SubscriptionCreate
from services import UserService, NotificationService

router = APIRouter(prefix="/users", tags=["Кабінет"])


@router.post("/register")
def register(data: UserRegister, service: UserService = Depends(get_user_service)):
    return service.register(data.name, data.email)


@router.post("/login")
def login(data: UserLogin, service: UserService = Depends(get_user_service)):
    return service.login(data.email)


@router.get("/{user_id}")
def get_user(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get(user_id)


@router.get("/{user_id}/prescriptions")
def get_prescriptions(user_id: int, service: UserService = Depends(get_user_service)):
    return service.list_prescriptions(user_id)


@router.post("/{user_id}/prescriptions")
def add_prescription(user_id: int, data: PrescriptionCreate, service: UserService = Depends(get_user_service)):
    return service.add_prescription(user_id, data)


@router.get("/{user_id}/subscriptions")
def get_subscriptions(user_id: int, service: UserService = Depends(get_user_service)):
    return service.list_subscriptions(user_id)


@router.post("/{user_id}/subscriptions")
def add_subscription(user_id: int, data: SubscriptionCreate, service: UserService = Depends(get_user_service)):
    return service.add_subscription(user_id, data)


@router.delete("/{user_id}/subscriptions/{sub_id}")
def delete_subscription(user_id: int, sub_id: int, service: UserService = Depends(get_user_service)):
    return service.delete_subscription(user_id, sub_id)


@router.get("/{user_id}/notifications")
def get_notifications(user_id: int, lat: float = config.DEFAULT_LAT, lon: float = config.DEFAULT_LON,
                      service: NotificationService = Depends(get_notification_service)):
    return service.build(user_id, lat, lon)
