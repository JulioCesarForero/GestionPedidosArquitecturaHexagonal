# services/order-service/tests/integration/test_adapters.py
import pytest
import pytest_asyncio
import asyncio
import asyncpg
import os
import json
from datetime import datetime

from domain.models import Order, OrderStatus
from domain.events import OrderCreated
from adapters.outbound.postgres_repository import PostgresOrderRepository
from adapters.outbound.postgres_saga_log import PostgresSagaLog


# PostgreSQL connection details for tests
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "orders_test")
PG_DSN = f"postgres://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"


@pytest_asyncio.fixture
async def pg_pool():
    # Create test database
    sys_conn = await asyncpg.connect(
        f"postgres://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres"
    )
    
    try:
        await sys_conn.execute(f"DROP DATABASE IF EXISTS {PG_DB}")
        await sys_conn.execute(f"CREATE DATABASE {PG_DB}")
    finally:
        await sys_conn.close()
    
    # Connect to test database and create tables
    pool = await asyncpg.create_pool(PG_DSN)
    
    async with pool.acquire() as conn:
        # Create tables for testing
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                modified_at TIMESTAMP NOT NULL,
                saga_id TEXT,
                metadata JSONB NOT NULL DEFAULT '{}',
                total_amount FLOAT NOT NULL
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id TEXT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price FLOAT NOT NULL
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS saga_log (
                saga_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TIMESTAMP NOT NULL,
                ended_at TIMESTAMP
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS saga_events (
                id SERIAL PRIMARY KEY,
                saga_id TEXT NOT NULL REFERENCES saga_log(saga_id),
                event_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data JSONB NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
    
    yield pool
    
    # Cleanup
    await pool.close()
    
    # Drop test database
    sys_conn = await asyncpg.connect(
        f"postgres://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/postgres"
    )
    
    try:
        await sys_conn.execute(f"DROP DATABASE IF EXISTS {PG_DB}")
    finally:
        await sys_conn.close()


@pytest_asyncio.fixture
async def order_repo(pg_pool):
    return PostgresOrderRepository(pg_pool)


@pytest_asyncio.fixture
async def saga_log_repo(pg_pool):
    return PostgresSagaLog(pg_pool)


@pytest_asyncio.fixture
async def sample_order():
    order = Order(
        id="test-order-id",
        customer_id="test-customer-id",
        status=OrderStatus.CREATED,
        saga_id="test-saga-id"
    )
    
    order.add_item(
        product_id="product-1",
        quantity=2,
        unit_price=10.0
    )
    
    order.add_item(
        product_id="product-2",
        quantity=1,
        unit_price=20.0
    )
    
    return order


@pytest.mark.asyncio
async def test_postgres_order_repository(order_repo, sample_order):
    # Test saving an order
    await order_repo.save(sample_order)
    
    # Test retrieving the order
    retrieved_order = await order_repo.get_by_id(sample_order.id)
    assert retrieved_order is not None
    assert retrieved_order.id == sample_order.id
    assert retrieved_order.customer_id == sample_order.customer_id
    assert retrieved_order.status == sample_order.status
    assert len(retrieved_order.items) == 2
    assert retrieved_order.total_amount == 40.0
    
    # Test retrieving by customer ID
    customer_orders = await order_repo.get_by_customer_id(sample_order.customer_id)
    assert len(customer_orders) == 1
    assert customer_orders[0].id == sample_order.id
    
    # Test updating the order
    retrieved_order.update_status(OrderStatus.PAYMENT_CONFIRMED)
    await order_repo.update(retrieved_order)
    
    updated_order = await order_repo.get_by_id(sample_order.id)
    assert updated_order.status == OrderStatus.PAYMENT_CONFIRMED
    
    # Test deleting the order
    await order_repo.delete(sample_order.id)
    
    deleted_order = await order_repo.get_by_id(sample_order.id)
    assert deleted_order is None


@pytest.mark.asyncio
async def test_postgres_saga_log(saga_log_repo, sample_order):
    # Test starting a saga
    await saga_log_repo.start_saga(sample_order.saga_id, sample_order.id)
    
    # Create an event
    event = OrderCreated(
        order_id=sample_order.id,
        customer_id=sample_order.customer_id,
        total_amount=sample_order.total_amount,
        saga_id=sample_order.saga_id
    )
    
    # Test logging an event
    await saga_log_repo.log_event(sample_order.saga_id, event)
    
    # Test retrieving saga events
    saga_events = await saga_log_repo.get_saga_events(sample_order.saga_id)
    assert len(saga_events) > 0
    assert "events" in saga_events
    assert len(saga_events["events"]) == 1
    assert saga_events["events"][0]["event_type"] == "order_created"
    
    # Test ending a saga
    await saga_log_repo.end_saga(sample_order.saga_id, True)
    
    # Check saga status
    saga_updated = await saga_log_repo.get_saga_events(sample_order.saga_id)
    assert saga_updated["status"] == "COMPLETED"
    assert saga_updated["ended_at"] is not None