
import asyncio
import os
import json
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractIncomingMessage
from . import models, routes
from .db import engine


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Product Service",
    description="Product management and inventory control",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routes.router, prefix="/products", tags=["products"])


@app.get("/")
async def root():
    
    return {"message": "Product Service is running"}


@app.get("/health")
async def health_check():
    
    return {"status": "ok", "service": "product-service"}



async def consume_order_events():
    
    try:
        connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://app:app@localhost:5672/"))
        channel = await connection.channel()
        
      
        exchange = await channel.declare_exchange("order_events", "topic", durable=True)
        queue = await channel.declare_queue("product_service_queue", durable=True)
        await queue.bind(exchange, "order.created")
        
        async def process_message(message: AbstractIncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    logger.info(f"Received order event: {data}")
                    
                   
                    if message.routing_key == "order.created":
                        order_id = data.get("order_id")
                        items = data.get("items", [])
                        
                      
                        from .db import SessionLocal
                        from .models import Product
                        
                        db = SessionLocal()
                        try:
                            
                            success = True
                            reason = ""
                            
                            for item in items:
                                product = db.query(Product).filter(Product.id == item["product_id"]).first()
                                if not product:
                                    success = False
                                    reason = f"Product {item['product_id']} not found"
                                    break
                                if product.quantity < item["quantity"]:
                                    success = False
                                    reason = f"Insufficient inventory for product {item['product_id']}"
                                    break
                            
                            if success:
                             
                                for item in items:
                                    product = db.query(Product).filter(Product.id == item["product_id"]).first()
                                    product.quantity -= item["quantity"]
                                db.commit()
                                await publish_event("inventory.reserved", {"order_id": order_id})
                            else:
                                await publish_event("inventory.failed", {"order_id": order_id, "reason": reason})
                        except Exception as e:
                            db.rollback()
                            await publish_event("inventory.failed", {"order_id": order_id, "reason": str(e)})
                        finally:
                            db.close()
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        
        await queue.consume(process_message)
        logger.info("Product service started consuming order events")
        
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")


async def publish_event(event_type: str, data: dict):
    """Publish event to RabbitMQ"""
    try:
        connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://app:app@localhost:5672/"))
        channel = await connection.channel()
        
        exchange = await channel.declare_exchange("order_events", "topic", durable=True)
        
        message = Message(
            json.dumps(data).encode(),
            delivery_mode=2  
        )
        
        await exchange.publish(message, routing_key=event_type)
        logger.info(f"Published event: {event_type} - {data}")
        
        await connection.close()
        
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")


@app.on_event("startup")
async def startup_event():
    """Start RabbitMQ consumer on startup"""
    asyncio.create_task(consume_order_events())
