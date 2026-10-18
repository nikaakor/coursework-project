"""Composition root: збирає сервіси з репозиторіїв для кожного запиту (Dependency Injection)."""
from fastapi import Depends, Header
from sqlalchemy.orm import Session

import config
from database import get_db
from exceptions import ForbiddenError
from repositories import (ProductRepository, PromotionRepository, PharmacyRepository, UserRepository,
                          PrescriptionRepository, SubscriptionRepository, NotificationRepository,
                          OrderRepository)
from services import (CatalogService, PharmacyService, UserService, NotificationService,
                      OrderService, AdminService, AdminOrderService, ReportService)


def require_admin(x_admin_key: str = Header(default="")):
    if x_admin_key != config.ADMIN_KEY:
        raise ForbiddenError("Невірний ключ адміністратора")


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(ProductRepository(db), PromotionRepository(db))


def get_pharmacy_service(db: Session = Depends(get_db)) -> PharmacyService:
    return PharmacyService(PharmacyRepository(db), ProductRepository(db))


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db), ProductRepository(db),
                       PrescriptionRepository(db), SubscriptionRepository(db))


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(get_user_service(db), SubscriptionRepository(db), NotificationRepository(db),
                               PromotionRepository(db), get_pharmacy_service(db))


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    return OrderService(UserRepository(db), ProductRepository(db), PharmacyRepository(db),
                        PromotionRepository(db), PrescriptionRepository(db), SubscriptionRepository(db),
                        OrderRepository(db), NotificationRepository(db))


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(ProductRepository(db), PharmacyRepository(db), PromotionRepository(db),
                        UserRepository(db), OrderRepository(db))


def get_admin_order_service(db: Session = Depends(get_db)) -> AdminOrderService:
    return AdminOrderService(OrderRepository(db), UserRepository(db), ProductRepository(db),
                             PharmacyRepository(db), NotificationRepository(db))


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(OrderRepository(db), ProductRepository(db), UserRepository(db), PharmacyRepository(db))
