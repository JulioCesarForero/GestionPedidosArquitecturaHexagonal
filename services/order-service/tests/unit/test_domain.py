# services/order-service/tests/unit/test_domain.py
import pytest
from datetime import datetime
from domain.models import Order, OrderItem, OrderStatus


def test_order_creation():
    order = Order(
        customer_id="customer-123",
    )
    
    assert order.id is not None
    assert order.customer_id == "customer-123"
    assert order.status == OrderStatus.CREATED
    assert isinstance(order.created_at, datetime)
    assert isinstance(order.modified_at, datetime)
    assert len(order.items) == 0
    assert order.total_amount == 0


def test_add_item():
    order = Order(
        customer_id="customer-123",
    )
    
    order.add_item(
        product_id="product-1",
        quantity=2,
        unit_price=10.0
    )
    
    assert len(order.items) == 1
    assert order.items[0].product_id == "product-1"
    assert order.items[0].quantity == 2
    assert order.items[0].unit_price == 10.0
    assert order.items[0].total_price == 20.0
    assert order.total_amount == 20.0


def test_multiple_items():
    order = Order(
        customer_id="customer-123",
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
    
    assert len(order.items) == 2
    assert order.total_amount == 40.0


def test_update_status():
    order = Order(
        customer_id="customer-123",
    )
    
    original_modified_at = order.modified_at
    
    # Wait a bit to ensure the modified timestamp changes
    import time
    time.sleep(0.001)
    
    order.update_status(OrderStatus.PENDING_PAYMENT)
    
    assert order.status == OrderStatus.PENDING_PAYMENT
    assert order.modified_at > original_modified_at


def test_cancel_order():
    order = Order(
        customer_id="customer-123",
        status=OrderStatus.PAYMENT_CONFIRMED
    )
    
    order.cancel()
    
    assert order.status == OrderStatus.CANCELLED


def test_cannot_cancel_shipped_order():
    order = Order(
        customer_id="customer-123",
        status=OrderStatus.SHIPPED
    )
    
    with pytest.raises(ValueError):
        order.cancel()


def test_to_dict():
    order = Order(
        id="test-order-id",
        customer_id="customer-123",
        status=OrderStatus.CREATED,
    )
    
    order.add_item(
        product_id="product-1",
        quantity=2,
        unit_price=10.0
    )
    
    order_dict = order.to_dict()
    
    assert order_dict["id"] == "test-order-id"
    assert order_dict["customer_id"] == "customer-123"
    assert order_dict["status"] == "CREATED"
    assert len(order_dict["items"]) == 1
    assert order_dict["total_amount"] == 20.0


def test_from_dict():
    order_dict = {
        "id": "test-order-id",
        "customer_id": "customer-123",
        "status": "PAYMENT_CONFIRMED",
        "created_at": "2023-01-01T12:00:00",
        "modified_at": "2023-01-01T12:30:00",
        "saga_id": "test-saga-id",
        "metadata": {"payment_id": "payment-123"},
        "items": [
            {
                "product_id": "product-1",
                "quantity": 2,
                "unit_price": 10.0
            },
            {
                "product_id": "product-2",
                "quantity": 1,
                "unit_price": 20.0
            }
        ]
    }
    
    order = Order.from_dict(order_dict)
    
    assert order.id == "test-order-id"
    assert order.customer_id == "customer-123"
    assert order.status == OrderStatus.PAYMENT_CONFIRMED
    assert order.saga_id == "test-saga-id"
    assert order.metadata == {"payment_id": "payment-123"}
    assert len(order.items) == 2
    assert order.total_amount == 40.0

