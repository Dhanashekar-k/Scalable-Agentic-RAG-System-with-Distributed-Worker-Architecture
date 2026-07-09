"""
RabbitMQ client for agent step execution queue.
Used ONLY for Agentic RAG step-by-step execution.
"""
import json
import asyncio
from typing import Optional, Callable
from aio_pika import connect_robust, Message, Channel, Queue, Connection
from aio_pika.abc import AbstractIncomingMessage
from config.settings import settings
from models.schemas import AgentStep


class RabbitMQClient:
    """Async RabbitMQ client for agent step queue."""
    
    def __init__(self):
        self.connection: Optional[Connection] = None
        self.channel: Optional[Channel] = None
        self.queue: Optional[Queue] = None
    
    async def connect(self):
        """Initialize RabbitMQ connection and declare queue."""
        url = (
            f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASSWORD}"
            f"@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
        )
        
        self.connection = await connect_robust(url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=1)  # One message at a time per worker
        
        # Declare durable queue
        self.queue = await self.channel.declare_queue(
            settings.RABBITMQ_QUEUE,
            durable=True
        )
    
    async def disconnect(self):
        """Close RabbitMQ connections."""
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
    
    async def publish_step(self, step: AgentStep):
        """
        Publish a single agent step to the queue.
        Called by the orchestrator after LangGraph planning.
        """
        message_body = step.model_dump_json()
        message = Message(
            body=message_body.encode(),
            delivery_mode=2,  # Persistent
            content_type="application/json"
        )
        
        await self.channel.default_exchange.publish(
            message,
            routing_key=settings.RABBITMQ_QUEUE
        )
    
    async def consume_steps(
        self,
        callback: Callable[[AgentStep], None]
    ):
        """
        Start consuming agent steps.
        Workers use this to process steps one by one.
        """
        async def process_message(message: AbstractIncomingMessage):
            async with message.process():
                try:
                    # Deserialize step
                    step_dict = json.loads(message.body.decode())
                    step = AgentStep(**step_dict)
                    
                    # Execute callback
                    await callback(step)
                    
                    # ACK handled by context manager
                except Exception as e:
                    # Log error but ACK to avoid infinite retries
                    # Retry logic is handled by step.attempt counter
                    print(f"Error processing step: {e}")
        
        await self.queue.consume(process_message)
    
    async def health_check(self) -> bool:
        """Check RabbitMQ connection health."""
        try:
            return self.connection and not self.connection.is_closed
        except Exception:
            return False


# Global RabbitMQ client instance
rabbitmq_client = RabbitMQClient()
