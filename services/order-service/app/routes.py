
import httpx
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, db, events

router = APIRouter()


async def get_user_from_token(token: str) -> dict:
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{os.getenv('USER_SERVICE_URL', 'http://localhost:8001')}/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )


async def get_product_prices(items: List[schemas.OrderItemCreate]) -> List[dict]:
    
    try:
        async with httpx.AsyncClient() as client:
            product_prices = {}
            for item in items:
                response = await client.get(
                    f"{os.getenv('PRODUCT_SERVICE_URL', 'http://localhost:8002')}/products/{item.product_id}"
                )
                if response.status_code == 200:
                    product_data = response.json()
                    product_prices[item.product_id] = product_data["price"]
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Product {item.product_id} not found"
                    )
            return product_prices
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service unavailable"
        )


@router.post("/", response_model=schemas.OrderResponse)
async def create_order(
    order: schemas.OrderCreate,
    db_session: Session = Depends(db.get_db)
):
    """Create a new order"""
    existing_order = db_session.query(models.Order).filter(
        models.Order.idempotency_key == order.idempotency_key
    ).first()
    
    if existing_order:
        return existing_order
    
    
    user_id = 1  
    
    
    product_prices = await get_product_prices(order.items)
    
    
    total_amount = sum(
        item.quantity * product_prices[item.product_id] 
        for item in order.items
    )
    
   
    db_order = models.Order(
        user_id=user_id,
        status="pending",
        total_amount=total_amount,
        idempotency_key=order.idempotency_key
    )
    db_session.add(db_order)
    db_session.commit()
    db_session.refresh(db_order)
    
  
    for item in order.items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=product_prices[item.product_id]
        )
        db_session.add(db_item)
    
    db_session.commit()
    db_session.refresh(db_order)
    
    
    await events.publish_event("order.created", {
        "order_id": db_order.id,
        "items": [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in order.items
        ]
    })
    
    return db_order


@router.get("/{order_id}", response_model=schemas.OrderResponse)
async def get_order(order_id: int, db_session: Session = Depends(db.get_db)):
    """Get order by ID"""
    order = db_session.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return order


@router.get("/", response_model=List[schemas.OrderResponse])
async def list_orders(
    user_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db_session: Session = Depends(db.get_db)
):
    
    query = db_session.query(models.Order)
    if user_id:
        query = query.filter(models.Order.user_id == user_id)
    
    orders = query.offset(skip).limit(limit).all()
    return orders


@router.put("/{order_id}", response_model=schemas.OrderResponse)
async def update_order(
    order_id: int,
    order_update: schemas.OrderUpdate,
    db_session: Session = Depends(db.get_db)
):
   
    order = db_session.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    update_data = order_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)
    
    db_session.commit()
    db_session.refresh(order)
    return order


@router.get("/health")
async def health_check():
   
    return {"status": "ok", "service": "order-service"}
