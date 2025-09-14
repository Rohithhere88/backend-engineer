
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, routes
from .db import engine

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="User Service",
    description="User registration, authentication, and profile management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/users", tags=["users"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "User Service is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "user-service"}
