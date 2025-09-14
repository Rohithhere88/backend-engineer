
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, db

router = APIRouter()


@router.post("/", response_model=schemas.ProductResponse)
async def create_product(product: schemas.ProductCreate, db_session: Session = Depends(db.get_db)):
    """Create a new product"""
    db_product = models.Product(
        name=product.name,
        description=product.description,
        price=product.price,
        quantity=product.quantity
    )
    db_session.add(db_product)
    db_session.commit()
    db_session.refresh(db_product)
    return db_product


@router.get("/", response_model=List[schemas.ProductResponse])
async def list_products(skip: int = 0, limit: int = 100, db_session: Session = Depends(db.get_db)):
    """List all products"""
    products = db_session.query(models.Product).offset(skip).limit(limit).all()
    return products


@router.get("/{product_id}", response_model=schemas.ProductResponse)
async def get_product(product_id: int, db_session: Session = Depends(db.get_db)):
    """Get product by ID"""
    product = db_session.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.put("/{product_id}", response_model=schemas.ProductResponse)
async def update_product(
    product_id: int, 
    product_update: schemas.ProductUpdate, 
    db_session: Session = Depends(db.get_db)
):
    """Update product"""
    product = db_session.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db_session.commit()
    db_session.refresh(product)
    return product


@router.post("/reserve-inventory")
async def reserve_inventory(
    reservation: schemas.InventoryReservationRequest,
    db_session: Session = Depends(db.get_db)
):
    """Reserve inventory for an order"""
    try:
        
        for item in reservation.items:
            product = db_session.query(models.Product).filter(models.Product.id == item.product_id).first()
            if not product:
                return {"success": False, "reason": f"Product {item.product_id} not found"}
            if product.quantity < item.quantity:
                return {"success": False, "reason": f"Insufficient inventory for product {item.product_id}"}
        
       
        for item in reservation.items:
            product = db_session.query(models.Product).filter(models.Product.id == item.product_id).first()
            product.quantity -= item.quantity
        
        db_session.commit()
        return {"success": True, "order_id": reservation.order_id}
    
    except Exception as e:
        db_session.rollback()
        return {"success": False, "reason": str(e)}


@router.post("/release-inventory")
async def release_inventory(
    reservation: schemas.InventoryReservationRequest,
    db_session: Session = Depends(db.get_db)
):
    """Release reserved inventory"""
    try:
        for item in reservation.items:
            product = db_session.query(models.Product).filter(models.Product.id == item.product_id).first()
            if product:
                product.quantity += item.quantity
        
        db_session.commit()
        return {"success": True, "order_id": reservation.order_id}
    
    except Exception as e:
        db_session.rollback()
        return {"success": False, "reason": str(e)}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "product-service"}
