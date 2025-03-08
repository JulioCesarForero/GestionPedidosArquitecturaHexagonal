# services/order-service/tests/conftest.py
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock
import json
from datetime import datetime

from domain.models import Order, OrderItem, OrderStatus
from application.ports.repositories import OrderRepository
from application.ports.message_bus import MessagePublisher, SagaLog


# Mock classes
class MockOrderRepository(OrderRepository):
    def __init__(self):
        self.orders = {}
    
    async def save(self, order: Order) -> None:
        self.orders[order.id] = order
    
    async def get_by_id(self, order_id: str) -> Order:
        return self.orders.get(order_id)
    
    async def get_by_customer_id(self, customer_id: str) -> list:
        return [order for order in self.orders.values() if order.customer_id == customer_id]
    
    async def update(self, order: Order) -> None:
        self.orders[order.id] = order
    
    async def delete(self, order_id: str) -> None:
        if order_id in self.orders:
            del self.orders[order_id]


class MockMessagePublisher(MessagePublisher):
    def __init__(self):
        self.published_events = []
    
    async def publish(self, event, topic: str) -> None:
        self.published_events.append((event, topic, None))
    
    async def publish_with_key(self, event, topic: str, key: str) -> None:
        self.published_events.append((event, topic, key))


class MockSagaLog(SagaLog):
    def __init__(self):
        self.sagas = {}
        self.events = {}
    
    async def start_saga(self, saga_id: str, order_id: str) -> None:
        self.sagas[saga_id] = {
            "order_id": order_id,
            "status": "STARTED",
            "started_at": datetime.now(),
            "ended_at": None
        }
        self.events[saga_id] = []
    
    async def log_event(self, saga_id: str, event) -> None:
        if saga_id not in self.events:
            self.events[saga_id] = []
        self.events[saga_id].append(event)
    
    async def end_saga(self, saga_id: str, success: bool) -> None:
        if saga_id in self.sagas:
            self.sagas[saga_id]["status"] = "COMPLETED" if success else "FAILED"
            self.sagas[saga_id]["ended_at"] = datetime.now()
    
    async def get_saga_events(self, saga_id: str) -> list:
        return [
            {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.to_dict()
            }
            for event in self.events.get(saga_id, [])
        ]


# Fixtures
@pytest.fixture
def order_repository():
    return MockOrderRepository()


@pytest.fixture
def message_publisher():
    return MockMessagePublisher()


@pytest.fixture
def saga_log():
    return MockSagaLog()


@pytest.fixture
def sample_order():
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
