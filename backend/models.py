from datetime import date, datetime
from sqlalchemy import (Column, Integer, String, Float, Boolean, ForeignKey,
                        Date, DateTime, UniqueConstraint)
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    loyalty_type = Column(String, default="regular")  # regular | social | premium
    bonus_points = Column(Float, default=0.0)

    orders = relationship("Order", back_populates="user")
    prescriptions = relationship("Prescription", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, index=True, nullable=False) 
    manufacturer = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    is_prescription = Column(Boolean, default=False)
    is_social = Column(Boolean, default=False) 
    stock_quantity = Column(Integer, default=0) 
    form_type = Column(String, default="Таблетки")
    active_ingredient = Column(String, default="")
    description = Column(String, default="")
    dosage_info = Column(String, default="")
    image_url = Column(String, default="")


class Pharmacy(Base):
    __tablename__ = "pharmacies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)


class PharmacyStock(Base):
    """Залишки конкретного товару в конкретній аптеці (для самовивозу/бронювання)."""
    __tablename__ = "pharmacy_stock"
    __table_args__ = (UniqueConstraint("pharmacy_id", "product_id"),)

    id = Column(Integer, primary_key=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=0)


class Promotion(Base):
    """Акції та сезонні знижки: на товар або на категорію, у межах дат."""
    __tablename__ = "promotions"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String, default="")
    discount_percent = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    code = Column(String, nullable=False)
    doctor = Column(String, default="")
    valid_until = Column(Date, nullable=False)
    is_used = Column(Boolean, default=False)

    user = relationship("User", back_populates="prescriptions")
    product = relationship("Product")


class Subscription(Base):
    """kind='regular' — нагадування про регулярний препарат (кожні N днів);
       kind='watch'   — сповістити, коли товар з'явиться в найближчій аптеці."""
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "product_id", "kind"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    kind = Column(String, nullable=False)
    interval_days = Column(Integer, nullable=True)
    last_order_date = Column(Date, default=date.today)

    user = relationship("User", back_populates="subscriptions")
    product = relationship("Product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    pharmacy_id = Column(Integer, ForeignKey("pharmacies.id"), nullable=True)
    address = Column(String, default="")
    delivery_type = Column(String, default="pickup")
    subtotal = Column(Float, default=0.0)
    discount_total = Column(Float, default=0.0)
    delivery_fee = Column(Float, default=0.0)
    bonus_spent = Column(Float, default=0.0)
    bonus_earned = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)
    status = Column(String, default="new")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    pharmacy = relationship("Pharmacy")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(String, default="order")
    message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
