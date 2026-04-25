import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, desc, asc, and_
from sqlalchemy.orm import Session, joinedload

from app.models import productmodels, shopmodels

logger = logging.getLogger(__name__)

PRICE_CHANGE_THRESHOLD = Decimal("10.0")


def get_or_create_product(
    db_session: Session,
    url: str,
    name: str,
    shop_id: int,
    image_url: Optional[str] = None,
    current_price: Optional[str] = None,
    price_per_unit: Optional[str] = None,
) -> productmodels.Product:
    product = db_session.query(productmodels.Product).filter(
        productmodels.Product.url == url
    ).first()
    
    if not product:
        product = productmodels.Product(
            url=url,
            name=name,
            shop_id=shop_id,
            image_url=image_url,
        )
        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)
    
    if current_price:
        try:
            price_value = Decimal(str(current_price).replace("£", "").replace(",", "").strip())
            update_product_price(db_session, product, price_value, price_per_unit)
        except Exception as e:
            logger.warning(f"Failed to parse price for product {url}: {e}")
    
    return product


def update_product_price(
    db_session: Session,
    product: productmodels.Product,
    new_price: Decimal,
    price_per_unit: Optional[str] = None,
) -> bool:
    if product.current_price is not None:
        old_price = product.current_price
        if old_price > Decimal("0"):
            price_change = abs(new_price - old_price) / old_price * Decimal("100")
            if price_change >= PRICE_CHANGE_THRESHOLD:
                product.previous_price = old_price
                product.current_price = new_price
                create_price_history(db_session, product, new_price, price_per_unit)
                create_price_change_notifications(
                    db_session, product, old_price, new_price, price_change
                )
                db_session.commit()
                return True
    
    if product.current_price is None:
        product.current_price = new_price
        create_price_history(db_session, product, new_price, price_per_unit)
        db_session.commit()
    
    return False


def create_price_history(
    db_session: Session,
    product: productmodels.Product,
    price: Decimal,
    price_per_unit: Optional[str] = None,
) -> productmodels.PriceHistory:
    price_history = productmodels.PriceHistory(
        product_id=product.id,
        price=price,
        price_per_unit=price_per_unit,
    )
    db_session.add(price_history)
    db_session.flush()
    return price_history


def create_price_change_notifications(
    db_session: Session,
    product: productmodels.Product,
    old_price: Decimal,
    new_price: Decimal,
    price_change_percent: Decimal,
):
    watchlist_items = db_session.query(productmodels.UserWatchlist).filter(
        productmodels.UserWatchlist.product_id == product.id,
        productmodels.UserWatchlist.is_active == True
    ).all()
    
    for item in watchlist_items:
        price_direction = "降价" if new_price < old_price else "涨价"
        notification = productmodels.Notification(
            user_id=item.user_id,
            title=f"商品{price_direction}提醒",
            message=f"您关注的商品 \"{product.name}\" {price_direction}了{price_change_percent:.2f}%，价格从 £{old_price} 变为 £{new_price}",
            product_id=product.id,
            notification_type="price_change",
            old_price=old_price,
            new_price=new_price,
            price_change_percent=price_change_percent,
        )
        db_session.add(notification)
    
    db_session.flush()


def get_price_history_daily(
    db_session: Session,
    product_id: int,
    days: int = 30,
) -> List[Dict[str, Any]]:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    results = db_session.query(
        func.date(productmodels.PriceHistory.recorded_at).label("date"),
        func.min(productmodels.PriceHistory.price).label("min_price"),
        func.avg(productmodels.PriceHistory.price).label("avg_price"),
        func.max(productmodels.PriceHistory.price).label("max_price"),
    ).filter(
        productmodels.PriceHistory.product_id == product_id,
        productmodels.PriceHistory.recorded_at >= start_date,
        productmodels.PriceHistory.recorded_at <= end_date,
    ).group_by(
        func.date(productmodels.PriceHistory.recorded_at)
    ).order_by(
        func.date(productmodels.PriceHistory.recorded_at)
    ).all()
    
    return [
        {
            "date": str(row.date),
            "min_price": str(row.min_price),
            "avg_price": str(row.avg_price),
            "max_price": str(row.max_price),
        }
        for row in results
    ]


def get_product_by_id(db_session: Session, product_id: int) -> Optional[productmodels.Product]:
    return db_session.query(productmodels.Product).filter(
        productmodels.Product.id == product_id
    ).first()


def get_product_by_url(db_session: Session, url: str) -> Optional[productmodels.Product]:
    return db_session.query(productmodels.Product).filter(
        productmodels.Product.url == url
    ).first()


def get_products(
    db_session: Session,
    offset: int = 0,
    limit: int = 100,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    shop_ids: Optional[List[int]] = None,
) -> List[productmodels.Product]:
    query = db_session.query(productmodels.Product)
    
    if min_price is not None:
        query = query.filter(productmodels.Product.current_price >= min_price)
    
    if max_price is not None:
        query = query.filter(productmodels.Product.current_price <= max_price)
    
    if shop_ids:
        query = query.filter(productmodels.Product.shop_id.in_(shop_ids))
    
    if sort_by:
        if sort_by == "price":
            sort_column = productmodels.Product.current_price
        elif sort_by == "updated_at":
            sort_column = productmodels.Product.updated_at
        elif sort_by == "created_at":
            sort_column = productmodels.Product.created_at
        else:
            sort_column = productmodels.Product.id
        
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(desc(productmodels.Product.id))
    
    return query.offset(offset).limit(limit).all()


def add_to_watchlist(
    db_session: Session,
    user_id: int,
    product_id: int,
) -> Optional[productmodels.UserWatchlist]:
    existing = db_session.query(productmodels.UserWatchlist).filter(
        productmodels.UserWatchlist.user_id == user_id,
        productmodels.UserWatchlist.product_id == product_id,
    ).first()
    
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db_session.commit()
        return existing
    
    product = get_product_by_id(db_session, product_id)
    if not product:
        return None
    
    watchlist_item = productmodels.UserWatchlist(
        user_id=user_id,
        product_id=product_id,
        is_active=True,
    )
    db_session.add(watchlist_item)
    db_session.commit()
    db_session.refresh(watchlist_item)
    return watchlist_item


def remove_from_watchlist(
    db_session: Session,
    user_id: int,
    product_id: int,
) -> bool:
    existing = db_session.query(productmodels.UserWatchlist).filter(
        productmodels.UserWatchlist.user_id == user_id,
        productmodels.UserWatchlist.product_id == product_id,
    ).first()
    
    if existing:
        existing.is_active = False
        db_session.commit()
        return True
    return False


def get_user_watchlist(
    db_session: Session,
    user_id: int,
) -> List[productmodels.UserWatchlist]:
    return db_session.query(productmodels.UserWatchlist).filter(
        productmodels.UserWatchlist.user_id == user_id,
        productmodels.UserWatchlist.is_active == True,
    ).options(
        joinedload(productmodels.UserWatchlist.product)
    ).all()


def is_product_in_watchlist(
    db_session: Session,
    user_id: int,
    product_id: int,
) -> bool:
    return db_session.query(productmodels.UserWatchlist).filter(
        productmodels.UserWatchlist.user_id == user_id,
        productmodels.UserWatchlist.product_id == product_id,
        productmodels.UserWatchlist.is_active == True,
    ).first() is not None


def get_notifications(
    db_session: Session,
    user_id: int,
    unread_only: bool = False,
    offset: int = 0,
    limit: int = 50,
) -> List[productmodels.Notification]:
    query = db_session.query(productmodels.Notification).filter(
        productmodels.Notification.user_id == user_id
    )
    
    if unread_only:
        query = query.filter(productmodels.Notification.is_read == False)
    
    query = query.order_by(desc(productmodels.Notification.created_at))
    
    return query.offset(offset).limit(limit).all()


def get_unread_notification_count(
    db_session: Session,
    user_id: int,
) -> int:
    return db_session.query(productmodels.Notification).filter(
        productmodels.Notification.user_id == user_id,
        productmodels.Notification.is_read == False,
    ).count()


def mark_notification_read(
    db_session: Session,
    user_id: int,
    notification_id: int,
) -> bool:
    notification = db_session.query(productmodels.Notification).filter(
        productmodels.Notification.id == notification_id,
        productmodels.Notification.user_id == user_id,
    ).first()
    
    if notification and not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db_session.commit()
        return True
    return False


def mark_all_notifications_read(
    db_session: Session,
    user_id: int,
) -> int:
    count = db_session.query(productmodels.Notification).filter(
        productmodels.Notification.user_id == user_id,
        productmodels.Notification.is_read == False,
    ).update(
        {
            productmodels.Notification.is_read: True,
            productmodels.Notification.read_at: datetime.utcnow(),
        },
        synchronize_session="fetch"
    )
    db_session.commit()
    return count
