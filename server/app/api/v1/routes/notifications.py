from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import productmodels, usermodels
from app.service import productservice

from ..dependencies.auth import RoleChecker, get_current_active_user

router = APIRouter()


@router.get(
    "/watchlist",
    response_model=List[productmodels.UserWatchlistRead],
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def get_watchlist(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
):
    """
    Get the user's watchlist.
    """
    watchlist = productservice.get_user_watchlist(
        db_session=db_session,
        user_id=current_user.id,
    )
    return watchlist


@router.post(
    "/watchlist",
    response_model=productmodels.UserWatchlistRead,
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def add_to_watchlist(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
    product_id: int = Body(..., embed=True),
):
    """
    Add a product to the user's watchlist.
    """
    watchlist_item = productservice.add_to_watchlist(
        db_session=db_session,
        user_id=current_user.id,
        product_id=product_id,
    )
    
    if not watchlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    return watchlist_item


@router.delete(
    "/watchlist/{product_id}",
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def remove_from_watchlist(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
    product_id: int,
):
    """
    Remove a product from the user's watchlist.
    """
    success = productservice.remove_from_watchlist(
        db_session=db_session,
        user_id=current_user.id,
        product_id=product_id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not in watchlist",
        )
    
    return {"message": "Removed from watchlist"}


@router.get(
    "/watchlist/check/{product_id}",
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def check_watchlist(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
    product_id: int,
):
    """
    Check if a product is in the user's watchlist.
    """
    is_in_watchlist = productservice.is_product_in_watchlist(
        db_session=db_session,
        user_id=current_user.id,
        product_id=product_id,
    )
    
    return {"in_watchlist": is_in_watchlist}


@router.get(
    "/",
    response_model=List[productmodels.NotificationRead],
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def get_notifications(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
    unread_only: bool = Query(False, description="Only return unread notifications"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Get the user's notifications.
    """
    notifications = productservice.get_notifications(
        db_session=db_session,
        user_id=current_user.id,
        unread_only=unread_only,
        offset=offset,
        limit=limit,
    )
    return notifications


@router.get(
    "/unread-count",
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def get_unread_notification_count(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
):
    """
    Get the count of unread notifications for the current user.
    """
    count = productservice.get_unread_notification_count(
        db_session=db_session,
        user_id=current_user.id,
    )
    return {"count": count}


@router.put(
    "/{notification_id}/read",
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def mark_notification_read(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
    notification_id: int,
):
    """
    Mark a specific notification as read.
    """
    success = productservice.mark_notification_read(
        db_session=db_session,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or already read",
        )
    
    return {"message": "Marked as read"}


@router.put(
    "/mark-all-read",
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def mark_all_notifications_read(
    *,
    db_session: Session = Depends(get_db),
    current_user: usermodels.User = Depends(get_current_active_user),
):
    """
    Mark all notifications as read for the current user.
    """
    count = productservice.mark_all_notifications_read(
        db_session=db_session,
        user_id=current_user.id,
    )
    
    return {"message": f"Marked {count} notifications as read", "count": count}
