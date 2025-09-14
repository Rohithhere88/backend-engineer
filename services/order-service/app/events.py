
import os
import json
import logging
import asyncio
from typing import Dict, Any
from aio_pika import connect_robust, Message
from aio_pika.abc import AbstractIncomingMessage
from .db import SessionLocal
from .models import Order

logger = logging.getLogger(__name__)


async def publish_event(event_type: str, data: Dict[str, Any]):
    
    try:
        connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://app:app@localhost:5672/"))
        channel = await connection.channel()
        
        exchange = await channel.declare_exchange("order_events", "topic", durable=True)
        
        message = Message(
            json.dumps(data).encode(),
            delivery_mode=2  # Make message persistent
        )
        
        await exchange.publish(message, routing_key=event_type)
        logger.info(f"Published event: {event_type} - {data}")
        
        await connection.close()
        
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")


async def consume_inventory_events():
    
    try:
        connection = await connect_robust(os.getenv("RABBITMQ_URL", "amqp://app:app@localhost:5672/"))
        channel = await connection.channel()
        
        # Declare exchange and queue
        exchange = await channel.declare_exchange("order_events", "topic", durable=True)
        queue = await channel.declare_queue("order_service_queue", durable=True)
        await queue.bind(exchange, "inventory.reserved")
        await queue.bind(exchange, "inventory.failed")
        
        async def process_message(message: AbstractIncomingMessage):
            async with message.process():
                try:
                    data = json.loads(message.body.decode())
                    logger.info(f"Received inventory event: {data}")
                    
                    db = SessionLocal()
                    try:
                        order_id = data.get("order_id")
                        order = db.query(Order).filter(Order.id == order_id).first()
                        
                        if not order:
                            logger.error(f"Order {order_id} not found")
                            return
                        
                        if message.routing_key == "inventory.reserved":
                            # Update order status to confirmed
                            order.status = "confirmed"
                            db.commit()
                            logger.info(f"Order {order_id} confirmed")
                            
                        elif message.routing_key == "inventory.failed":
                            # Update order status to cancelled
                            order.status = "cancelled"
                            db.commit()
                            logger.info(f"Order {order_id} cancelled: {data.get('reason', 'Unknown reason')}")
                    
                    finally:
                        db.close()
                    
                except Exception as e:
                    logger.error(f"Error processing inventory event: {e}")
        
        await queue.consume(process_message)
        logger.info("Order service started consuming inventory events")
        
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")


async def start_event_consumer():
    
    asyncio.create_task(consume_inventory_events())
