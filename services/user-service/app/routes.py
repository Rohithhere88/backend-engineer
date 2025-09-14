
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, auth, db

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db_session: Session = Depends(db.get_db)):
    """Register a new user"""
    # Check if user already exists
    db_user = db_session.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        password_hash=hashed_password,
        name=user.name
    )
    db_session.add(db_user)
    db_session.commit()
    db_session.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=schemas.Token)
async def login_user(user: schemas.UserLogin, db_session: Session = Depends(db.get_db)):
    """Login user and return access token"""
    # Verify user credentials
    db_user = db_session.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
async def get_current_user(
    db_session: Session = Depends(db.get_db)
):
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="This endpoint requires proper token extraction from headers"
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "user-service"}
