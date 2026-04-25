from typing import List, Optional, Set
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import productmodels
from app.service import productservice, scraperservice, shopservice

from ..dependencies.auth import RoleChecker, get_current_active_user, user_role

router = APIRouter()


@router.get(
    "/",
    response_model=List[productmodels.ProductRead],
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def get_products(
    *,
    db_session: Session = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    min_price: Optional[str] = Query(None, description="Minimum price filter"),
    max_price: Optional[str] = Query(None, description="Maximum price filter"),
    sort_by: Optional[str] = Query(None, description="Sort by: price, updated_at, created_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    include: Optional[List[int]] = Query(None, description="Shop IDs to filter by"),
):
    """
    Retrieve a list of products with filtering and sorting.
    """
    min_price_dec = None
    max_price_dec = None
    
    if min_price:
        try:
            min_price_dec = Decimal(min_price.replace("£", "").replace(",", "").strip())
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid min_price format",
            )
    
    if max_price:
        try:
            max_price_dec = Decimal(max_price.replace("£", "").replace(",", "").strip())
        except:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid max_price format",
            )
    
    products = productservice.get_products(
        db_session=db_session,
        offset=offset,
        limit=limit,
        min_price=min_price_dec,
        max_price=max_price_dec,
        sort_by=sort_by,
        sort_order=sort_order,
        shop_ids=include,
    )
    
    return products


@router.get(
    "/{product_id}",
    response_model=productmodels.ProductRead,
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def get_product(
    *,
    db_session: Session = Depends(get_db),
    product_id: int,
):
    """
    Retrieve details about a specific product.
    """
    product = productservice.get_product_by_id(db_session=db_session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.get(
    "/{product_id}/price-history",
    response_model=List[productmodels.PriceHistoryDailyAggregate],
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
def get_product_price_history(
    *,
    db_session: Session = Depends(get_db),
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve"),
):
    """
    Retrieve daily price history for a product (daily minimum, average, maximum prices).
    """
    product = productservice.get_product_by_id(db_session=db_session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    return productservice.get_price_history_daily(
        db_session=db_session,
        product_id=product_id,
        days=days,
    )


@router.post(
    "/sync-from-listings",
    response_model=List[productmodels.ProductRead],
    dependencies=[Depends(RoleChecker(["admin", "user"]))],
)
async def sync_products_from_listings(
    *,
    db_session: Session = Depends(get_db),
    query: str = Query(..., description="The search term to query by."),
    limit: int = Query(10, description="The number of results to return.", ge=1, le=40),
    include: Set[int] = Query(..., description="Shop IDs to query for listings."),
):
    """
    Scrape listings and save/update products to database.
    """
    scraped_results = await scraperservice.query_scrapers(
        query=query, limit=limit, include=include
    )
    
    saved_products = []
    
    for shop_listings in scraped_results:
        if shop_listings.listings:
            for item in shop_listings.listings:
                if item.url and item.name:
                    product = productservice.get_or_create_product(
                        db_session=db_session,
                        url=item.url,
                        name=item.name,
                        shop_id=shop_listings.id,
                        image_url=item.image_url,
                        current_price=item.price,
                        price_per_unit=item.price_per_unit,
                    )
                    saved_products.append(product)
    
    db_session.commit()
    return saved_products
