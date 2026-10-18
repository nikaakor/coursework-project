"""Pydantic-схеми запитів (DTO)."""
from datetime import date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserLogin(BaseModel):
    email: str


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=99)


class OrderRequest(BaseModel):
    user_id: int
    items: List[CartItem]
    delivery_type: Literal["pickup", "courier"] = "pickup"
    pharmacy_id: Optional[int] = None     
    address: Optional[str] = None       
    use_bonuses: float = Field(default=0.0, ge=0)


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    category: Literal["Ліки", "Вітаміни", "Медичні вироби"]
    manufacturer: str = Field(min_length=1)
    price: float = Field(gt=0)
    is_prescription: bool = False
    is_social: bool = False
    stock_quantity: int = Field(default=0, ge=0)
    form_type: str = ""
    active_ingredient: str = ""
    description: str = ""
    dosage_info: str = ""
    image_url: Optional[str] = ""


class PrescriptionCreate(BaseModel):
    product_id: int
    code: str = Field(min_length=3)
    doctor: str = ""
    valid_until: date


class SubscriptionCreate(BaseModel):
    product_id: int
    kind: Literal["regular", "watch"]
    interval_days: Optional[int] = Field(default=None, ge=1, le=365)


class StockUpdate(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)


class PromotionCreate(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    description: str = ""
    discount_percent: float = Field(gt=0, le=90)
    category: Optional[str] = None
    product_id: Optional[int] = None
    date_from: date
    date_to: date


class LoyaltyUpdate(BaseModel):
    loyalty_type: Literal["regular", "social", "premium"]


class PharmacyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    address: str = Field(min_length=3, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class OrderStatusUpdate(BaseModel):
    status: Literal["processing", "shipped", "ready", "completed", "cancelled"]


class BonusAdjust(BaseModel):
    delta: float = Field(ge=-100000, le=100000)
