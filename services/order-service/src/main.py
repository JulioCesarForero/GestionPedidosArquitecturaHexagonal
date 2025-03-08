# services/order-service/src/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "order-service"}

@app.get("/")
async def root():
    return {"message": "Order Service API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# import logging
# import asyncio
# import argparse
# import sys
# from contextlib import asynccontextmanager

# import asyncpg
# import pulsar
# import uvicorn
# from fastapi import FastAPI

# from config import load_config
# from adapters.inbound.fastapi_app import create_app, Handlers
# from adapters.inbound.event_handlers import EventHandlers
# from adapters.outbound.postgres_repository import PostgresOrderRepository
# from adapters.outbound.postgres_saga_log import PostgresSagaLog
# from adapters.outbound.pulsar_event_publisher import PulsarMessagePublisher, PulsarMessageConsumer
# from application.commands.create_order import CreateOrderHandler
# from application.commands.cancel_order import CancelOrderHandler
# from application.queries.get_order import GetOrderHandler, GetCustomerOrdersHandler


# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.StreamHandler(sys.stdout),
#     ],
# )

# logger = logging.getLogger(__name__)


# async def create_tables(pool):
#     """Create database tables if they don't exist"""
#     async with pool.acquire() as conn:
#         # Create orders table
#         await conn.execute("""
#             CREATE TABLE IF NOT EXISTS orders (
#                 id TEXT PRIMARY KEY,
#                 customer_id TEXT NOT NULL,
#                 status TEXT NOT NULL,
#                 created_at TIMESTAMP NOT NULL,
#                 modified_at TIMESTAMP NOT NULL,
#                 saga_id TEXT,
#                 metadata JSONB NOT NULL DEFAULT '{}',
#                 total_amount FLOAT NOT NULL
#             )
#         """)
        
#         # Create order items table
#         await conn.execute("""
#             CREATE TABLE IF NOT EXISTS order_items (
#                 id SERIAL PRIMARY KEY,
#                 order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
#                 product_id TEXT NOT NULL,
#                 quantity INTEGER NOT NULL,
#                 unit_price FLOAT NOT NULL
#             )
#         """)
        
#         # Create saga log table
#         await conn.execute("""
#             CREATE TABLE IF NOT EXISTS saga_log (
#                 saga_id TEXT PRIMARY KEY,
#                 order_id TEXT NOT NULL,
#                 status TEXT NOT NULL,
#                 started_at TIMESTAMP NOT NULL,
#                 ended_at TIMESTAMP
#             )
#         """)
        
#         # Create saga events table
#         await conn.execute("""
#             CREATE TABLE IF NOT EXISTS saga_events (
#                 id SERIAL PRIMARY KEY,
#                 saga_id TEXT NOT NULL REFERENCES saga_log(saga_id),
#                 event_id TEXT NOT NULL,
#                 event_type TEXT NOT NULL,
#                 event_data JSONB NOT NULL,
#                 timestamp TIMESTAMP NOT NULL
#             )
#         """)
        
#         # Create indexes
#         await conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id)")
#         await conn.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")
#         await conn.execute("CREATE INDEX IF NOT EXISTS idx_saga_events_saga_id ON saga_events(saga_id)")


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Startup and shutdown events for FastAPI"""
#     # Load configuration
#     config = load_config()
#     logger.info(f"Starting {config.service_name} service")
    
#     # Create PostgreSQL connection pool
#     pg_pool = await asyncpg.create_pool(
#         dsn=config.postgresql.connection_string,
#         min_size=config.postgresql.min_size,
#         max_size=config.postgresql.max_size,
#     )
    
#     # Create database tables
#     await create_tables(pg_pool)
    
#     # Create Pulsar client
#     pulsar_client = pulsar.Client(config.pulsar.service_url)
    
#     # Create repositories and services
#     order_repository = PostgresOrderRepository(pg_pool)
#     saga_log = PostgresSagaLog(pg_pool)
#     message_publisher = PulsarMessagePublisher(pulsar_client)
#     message_consumer = PulsarMessageConsumer(pulsar_client, config.service_name)
    
#     # Create command and query handlers
#     create_order_handler = CreateOrderHandler(
#         order_repository=order_repository,
#         message_publisher=message_publisher,
#         saga_log=saga_log,
#     )
    
#     cancel_order_handler = CancelOrderHandler(
#         order_repository=order_repository,
#         message_publisher=message_publisher,
#         saga_log=saga_log,
#     )
    
#     get_order_handler = GetOrderHandler(
#         order_repository=order_repository,
#         saga_log=saga_log,
#     )
    
#     get_customer_orders_handler = GetCustomerOrdersHandler(
#         order_repository=order_repository,
#     )
    
#     # Create event handlers
#     event_handlers = EventHandlers(
#         order_repository=order_repository,
#         message_publisher=message_publisher,
#         saga_log=saga_log,
#     )
    
#     # Subscribe to required topics
#     await message_consumer.subscribe("payments", event_handlers.handle_payment_processed)
#     await message_consumer.subscribe("inventory", event_handlers.handle_inventory_allocated)
#     await message_consumer.subscribe("shipping", event_handlers.handle_order_shipped)
    
#     # Store handlers in app state
#     app.state.handlers = Handlers(
#         create_order_handler=create_order_handler,
#         cancel_order_handler=cancel_order_handler,
#         get_order_handler=get_order_handler,
#         get_customer_orders_handler=get_customer_orders_handler,
#     )
#     app.state.pg_pool = pg_pool
#     app.state.pulsar_client = pulsar_client
#     app.state.message_consumer = message_consumer
    
#     logger.info(f"{config.service_name} service started")
    
#     yield
    
#     # Cleanup resources
#     logger.info(f"Shutting down {config.service_name} service")
    
#     await message_consumer.close()
#     pulsar_client.close()
#     await pg_pool.close()
    
#     logger.info(f"{config.service_name} service stopped")


# async def main():
#     """Application entry point"""
#     # Parse command line arguments
#     parser = argparse.ArgumentParser(description="Order service")
#     parser.add_argument("--create-tables", action="store_true", help="Create database tables and exit")
#     args = parser.parse_args()
    
#     # Load configuration
#     config = load_config()
    
#     if args.create_tables:
#         # Create database tables only
#         pg_pool = await asyncpg.create_pool(dsn=config.postgresql.connection_string)
#         await create_tables(pg_pool)
#         await pg_pool.close()
#         logger.info("Database tables created")
#         return
    
#     # Create FastAPI application with lifespan
#     app = FastAPI(lifespan=lifespan)
#     api_app = create_app(None)  # Handlers will be injected in lifespan
    
#     # Mount API app
#     app.mount("/api", api_app)
    
#     # Run application with uvicorn
#     uvicorn.run(
#         app,
#         host=config.api.host,
#         port=config.api.port,
#         log_level="info",
#     )


# if __name__ == "__main__":
#     asyncio.run(main())