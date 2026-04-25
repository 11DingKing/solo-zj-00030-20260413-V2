from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from pydantic import validator
from sqlalchemy import Column, ForeignKey, Integer, String, Numeric, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .meta.pydanticbase import PydanticBase
from .meta.pydanticmixins import PydanticTS
from .meta.sqlalchemybase import SQLAlchemyBase
from .meta.sqlalchemymixins import SQLAlchemyIntPK, SQLAlchemyTS


class Product(SQLAlchemyTS, SQLAlchemyIntPK, SQLAlchemyBase):
    __tablename__ = "product"
    url = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    shop_id = Column(
        Integer, ForeignKey("shop.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    current_price = Column(Numeric(10, 2), nullable=True)
    previous_price = Column(Numeric(10, 2), nullable=True)
    
    shop = relationship("Shop")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    watchlist_items = relationship("UserWatchlist", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(SQLAlchemyTS, SQLAlchemyIntPK, SQLAlchemyBase):
    __tablename__ = "price_history"
    product_id = Column(
        Integer, ForeignKey("product.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    price = Column(Numeric(10, 2), nullable=False)
    price_per_unit = Column(String, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    product = relationship("Product", back_populates="price_history")


class UserWatchlist(SQLAlchemyTS, SQLAlchemyIntPK, SQLAlchemyBase):
    __tablename__ = "user_watchlist"
    user_id = Column(
        Integer, ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    product_id = Column(
        Integer, ForeignKey("product.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    product = relationship("Product", back_populates="watchlist_items")


class Notification(SQLAlchemyTS, SQLAlchemyIntPK, SQLAlchemyBase):
    __tablename__ = "notification"
    user_id = Column(
        Integer, ForeignKey("user.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    product_id = Column(
        Integer, ForeignKey("product.id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True
    )
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    notification_type = Column(String(50), default="price_change", nullable=False)
    old_price = Column(Numeric(10, 2), nullable=True)
    new_price = Column(Numeric(10, 2), nullable=True)
    price_change_percent = Column(Numeric(5, 2), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)


class ProductCreate(PydanticBase):
    url: str
    name: str
    image_url: Optional[str] = None
    shop_id: int
    current_price: Optional[str] = None
    
    @validator("current_price", pre=True)
    def parse_price(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, str):
            v = v.replace("£", "").replace(",", "").strip()
            try:
                return Decimal(v)
            except:
                return None
        return v


class ProductRead(PydanticTS, ProductCreate):
    id: int
    current_price: Optional[str] = None
    previous_price: Optional[str] = None
    
    @validator("current_price", "previous_price", pre=True)
    def format_price(cls, v):
        if v is None:
            return None
        return str(v)


class PriceHistoryRead(PydanticBase):
    id: int
    product_id: int
    price: str
    price_per_unit: Optional[str] = None
    recorded_at: datetime
    created_at: datetime
    
    @validator("price", pre=True)
    def format_price(cls, v):
        if v is None:
            return "0"
        return str(v)


class PriceHistoryDailyAggregate(PydanticBase):
    date: str
    min_price: str
    avg_price: str
    max_price: str
    
    @validator("min_price", "avg_price", "max_price", pre=True)
    def format_prices(cls, v):
        if v is None:
            return "0"
        return str(v)


class UserWatchlistCreate(PydanticBase):
    product_id: int


class UserWatchlistRead(PydanticTS):
    id: int
    user_id: int
    product_id: int
    is_active: bool
    product: Optional[ProductRead] = None


class NotificationRead(PydanticTS):
    id: int
    user_id: int
    title: str
    message: str
    product_id: Optional[int] = None
    is_read: bool
    notification_type: str
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    price_change_percent: Optional[str] = None
    read_at: Optional[datetime] = None
    
    @validator("old_price", "new_price", "price_change_percent", pre=True)
    def format_numeric(cls, v):
        if v is None:
            return None
        return str(v)


class NotificationMarkRead(PydanticBase):
    notification_id: int
