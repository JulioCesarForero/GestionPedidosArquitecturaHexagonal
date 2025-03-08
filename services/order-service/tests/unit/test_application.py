# services/order-service/tests/unit/test_application.py
import pytest
import pytest_asyncio
import uuid
from datetime import datetime

from domain.models import OrderStatus
from application.commands.create_order import CreateOrderCommand, CreateOrderHandler, CreateOrderItemDTO
from application.commands.cancel_order import CancelOrderCommand, CancelOrderHandler
from application.queries.get_order import GetOrderQuery, GetOrderHandler, GetCustomerOrdersQuery, GetCustomerOrdersHandler


@pytest_asyncio.fixture
async def create_order_handler(order_repository, message_publisher, saga_log):
    return CreateOrderHandler(
        order_repository=order_repository,
        message_publisher=message_publisher,
        saga_log=saga_log
    )


@pytest_asyncio.fixture
async def cancel_order_handler(order_repository, message_publisher, saga_log):
    return CancelOrderHandler(
        order_repository=order_repository,
        message_publisher=message_publisher,
        saga_log=saga_log
    )


@pytest_asyncio.fixture
async def get_order_handler(order_repository, saga_log):
    return GetOrderHandler(
        order_repository=order_repository,
        saga_log=saga_log
    )


@pytest_asyncio.fixture
async def get_customer_orders_handler(order_repository):
    return GetCustomerOrdersHandler(
        order_repository=order_repository
    )


@pytest.mark.asyncio
async def test_create_order_handler(create_order_handler, order_repository, message_publisher, saga_log):
    # Create the command
    command = CreateOrderCommand(
        customer_id="customer-123",
        items=[
            CreateOrderItemDTO(
                product_id="product-1",
                quantity=2,
                unit_price=10.0
            ),
            CreateOrderItemDTO(
                product_id="product-2",
                quantity=1,
                unit_price=20.0
            )
        ]
    )
    
    # Execute the handler
    result = await create_order_handler.handle(command)
    
    # Check the result
    assert "order_id" in result
    assert "saga_id" in result
    assert result["status"] == "PENDING_PAYMENT"
    
    # Verify order was saved
    order = await order_repository.get_by_id(result["order_id"])
    assert order is not None
    assert order.customer_id == "customer-123"
    assert len(order.items) == 2
    assert order.total_amount == 40.0
    assert order.status == OrderStatus.PENDING_PAYMENT
    
    # Verify saga was created
    assert result["saga_id"] in saga_log.sagas
    assert saga_log.sagas[result["saga_id"]]["order_id"] == result["order_id"]
    
    # Verify events were published
    assert len(message_publisher.published_events) == 2
    
    # First event should be order created
    event1, topic1, _ = message_publisher.published_events[0]
    assert event1.event_type == "order_created"
    assert event1.order_id == result["order_id"]
    assert topic1 == "orders"
    
    # Second event should be payment requested
    event2, topic2, _ = message_publisher.published_events[1]
    assert event2.event_type == "payment_requested"
    assert event2.order_id == result["order_id"]
    assert topic2 == "payments"


@pytest.mark.asyncio
async def test_cancel_order_handler(cancel_order_handler, order_repository, message_publisher, saga_log, sample_order):
    # Save the order
    await order_repository.save(sample_order)
    
    # Create the command
    command = CancelOrderCommand(
        order_id=sample_order.id,
        reason="Customer requested cancellation"
    )
    
    # Execute the handler
    result = await cancel_order_handler.handle(command)
    
    # Check the result
    assert result["success"] is True
    assert result["order_id"] == sample_order.id
    assert result["status"] == "CANCELLED"
    
    # Verify order was updated
    order = await order_repository.get_by_id(sample_order.id)
    assert order.status == OrderStatus.CANCELLED
    
    # Verify event was published
    assert len(message_publisher.published_events) == 1
    event, topic, _ = message_publisher.published_events[0]
    assert event.event_type == "order_cancelled"
    assert event.order_id == sample_order.id
    assert event.reason == "Customer requested cancellation"
    assert topic == "orders"


@pytest.mark.asyncio
async def test_get_order_handler(get_order_handler, order_repository, saga_log, sample_order):
    # Save the order
    await order_repository.save(sample_order)
    
    # Create the query
    query = GetOrderQuery(
        order_id=sample_order.id,
        include_saga_history=False
    )
    
    # Execute the handler
    result = await get_order_handler.handle(query)
    
    # Check the result
    assert result is not None
    assert result["id"] == sample_order.id
    assert result["customer_id"] == sample_order.customer_id
    assert result["status"] == sample_order.status.name
    assert len(result["items"]) == len(sample_order.items)
    assert "saga_history" not in result


@pytest.mark.asyncio
async def test_get_order_with_saga_history(get_order_handler, order_repository, saga_log, sample_order):
    # Save the order
    await order_repository.save(sample_order)
    
    # Start saga and log some events
    await saga_log.start_saga(sample_order.saga_id, sample_order.id)
    
    from domain.events import OrderCreated, PaymentRequested
    
    event1 = OrderCreated(
        order_id=sample_order.id,
        customer_id=sample_order.customer_id,
        total_amount=sample_order.total_amount,
        saga_id=sample_order.saga_id
    )
    
    event2 = PaymentRequested(
        order_id=sample_order.id,
        customer_id=sample_order.customer_id,
        amount=sample_order.total_amount,
        saga_id=sample_order.saga_id
    )
    
    await saga_log.log_event(sample_order.saga_id, event1)
    await saga_log.log_event(sample_order.saga_id, event2)
    
    # Create the query with saga history
    query = GetOrderQuery(
        order_id=sample_order.id,
        include_saga_history=True
    )
    
    # Execute the handler
    result = await get_order_handler.handle(query)
    
    # Check the result
    assert result is not None
    assert "saga_history" in result
    assert len(result["saga_history"]) == 2


@pytest.mark.asyncio
async def test_get_customer_orders_handler(get_customer_orders_handler, order_repository, sample_order):
    # Save the order
    await order_repository.save(sample_order)
    
    # Create another order for the same customer
    order2 = sample_order.from_dict(sample_order.to_dict())
    order2.id = str(uuid.uuid4())
    await order_repository.save(order2)
    
    # Create an order for another customer
    different_customer_order = sample_order.from_dict(sample_order.to_dict())
    different_customer_order.id = str(uuid.uuid4())
    different_customer_order.customer_id = "different-customer"
    await order_repository.save(different_customer_order)
    
    # Create the query
    query = GetCustomerOrdersQuery(
        customer_id=sample_order.customer_id
    )
    
    # Execute the handler
    result = await get_customer_orders_handler.handle(query)
    
    # Check the result
    assert result is not None
    assert result["customer_id"] == sample_order.customer_id
    assert result["total_orders"] == 2
    assert len(result["orders"]) == 2