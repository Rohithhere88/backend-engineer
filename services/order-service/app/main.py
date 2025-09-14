
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, routes, events
from .db import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Order Service",
    description="Order processing and management",
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
app.include_router(routes.router, prefix="/orders", tags=["orders"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Order Service is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "order-service"}


@app.on_event("startup")
async def startup_event():
    """Start event consumer on startup"""
    await events.start_event_consumer()
