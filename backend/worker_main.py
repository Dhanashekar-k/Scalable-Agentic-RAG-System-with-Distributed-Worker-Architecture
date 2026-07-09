"""
Worker startup script.
Run this separately to start RabbitMQ consumers.
"""
import asyncio
from database.redis_client import redis_client
from database.chroma_client import chroma_client
from database.neo4j_client import neo4j_client
from utils.rabbitmq_client import rabbitmq_client
from services.embedding_service import embedding_service
from services.agentic_rag.worker import agent_worker


async def main():
    """Initialize services and start worker."""
    print("🚀 Starting Agent Worker...")
    
    # Initialize connections
    await redis_client.connect()
    chroma_client.connect()
    await neo4j_client.connect()
    await rabbitmq_client.connect()
    
    # Load embedding model
    embedding_service.load_model()
    
    print("✅ Worker initialized, starting consumption...")
    
    try:
        # Start consuming
        await agent_worker.start()
    except KeyboardInterrupt:
        print("\n🛑 Stopping worker...")
    finally:
        # Cleanup
        await agent_worker.stop()
        await redis_client.disconnect()
        await neo4j_client.disconnect()
        await rabbitmq_client.disconnect()
        print("✅ Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
