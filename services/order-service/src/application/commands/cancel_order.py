# services/order-service/src/application/commands/cancel_order.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

from domain.models import OrderStatus
from domain.events import OrderCancelled
from application.ports.repositories import OrderRepository
from application.ports.message_bus import MessagePublisher, SagaLog


@dataclass
class CancelOrderCommand:
    order_id: str
    reason: str


class CancelOrderHandler:
    def __init__(
        self,
        order_repository: OrderRepository,
        message_publisher: MessagePublisher,
        saga_log: SagaLog,
    ):
        self.order_repository = order_repository
        self.message_publisher = message_publisher
        self.saga_log = saga_log
    
    async def handle(self, command: CancelOrderCommand) -> Dict[str, Any]:
        # Retrieve the order
        order = await self.order_repository.get_by_id(command.order_id)
        
        if not order:
            raise ValueError(f"Order with ID {command.order_id} not found")
        
        # Check if the order can be cancelled
        try:
            order.cancel()
        except ValueError as e:
            return {
                "success": False,
                "message": str(e),
            }
        
        # Update the order in the repository
        await self.order_repository.update(order)
        
        # Create an order cancelled event
        order_cancelled_event = OrderCancelled(
            order_id=order.id,
            reason=command.reason,
            saga_id=order.saga_id,
        )
        
        # Publish the event
        await self.message_publisher.publish(
            event=order_cancelled_event,
            topic="orders",
        )
        
        # Log the event in the saga (if saga exists)
        if order.saga_id:
            await self.saga_log.log_event(order.saga_id, order_cancelled_event)
            await self.saga_log.end_saga(order.saga_id, False)
        
        return {
            "success": True,
            "order_id": order.id,
            "status": order.status.name,
        }