import uuid
from dataclasses import dataclass
from typing import List, Dict, Any

from domain.models import Order, OrderItem, OrderStatus
from domain.events import OrderCreated, PaymentRequested
from application.ports.repositories import OrderRepository
from application.ports.message_bus import MessagePublisher, SagaLog


@dataclass
class CreateOrderItemDTO:
    product_id: str
    quantity: int
    unit_price: float


@dataclass
class CreateOrderCommand:
    customer_id: str
    items: List[CreateOrderItemDTO]


class CreateOrderHandler:
    def __init__(
        self,
        order_repository: OrderRepository,
        message_publisher: MessagePublisher,
        saga_log: SagaLog,
    ):
        self.order_repository = order_repository
        self.message_publisher = message_publisher
        self.saga_log = saga_log
    
    async def handle(self, command: CreateOrderCommand) -> Dict[str, Any]:
        # Create a new order with the provided data
        order = Order(
            customer_id=command.customer_id,
            status=OrderStatus.CREATED,
        )
        
        # Add items to the order
        for item in command.items:
            order.add_item(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )
        
        # Generate a SAGA ID for order orchestration
        saga_id = str(uuid.uuid4())
        order.saga_id = saga_id
        
        # Save the order to the repository
        await self.order_repository.save(order)
        
        # Start a new saga
        await self.saga_log.start_saga(saga_id, order.id)
        
        # Create the order created event
        order_created_event = OrderCreated(
            order_id=order.id,
            customer_id=order.customer_id,
            total_amount=order.total_amount,
            items={
                item.product_id: {
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in order.items
            },
            saga_id=saga_id,
        )
        
        # Publish the order created event
        await self.message_publisher.publish(
            event=order_created_event,
            topic="orders",
        )
        
        # Log the event in the saga
        await self.saga_log.log_event(saga_id, order_created_event)
        
        # Create the payment requested event
        payment_requested_event = PaymentRequested(
            order_id=order.id,
            customer_id=order.customer_id,
            amount=order.total_amount,
            saga_id=saga_id,
        )
        
        # Update order status
        order.update_status(OrderStatus.PENDING_PAYMENT)
        await self.order_repository.update(order)
        
        # Publish the payment requested event
        await self.message_publisher.publish(
            event=payment_requested_event,
            topic="payments",
        )
        
        # Log the event in the saga
        await self.saga_log.log_event(saga_id, payment_requested_event)
        
        return {
            "order_id": order.id,
            "saga_id": saga_id,
            "status": order.status.name,
        }

