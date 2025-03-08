# services/order-service/src/adapters/inbound/event_handlers.py
import logging
from typing import Dict, Any

from domain.models import OrderStatus
from domain.events import PaymentProcessed, InventoryAllocated, OrderShipped
from application.ports.repositories import OrderRepository
from application.ports.message_bus import MessagePublisher, SagaLog


class EventHandlers:
    def __init__(
        self,
        order_repository: OrderRepository,
        message_publisher: MessagePublisher,
        saga_log: SagaLog,
    ):
        self.order_repository = order_repository
        self.message_publisher = message_publisher
        self.saga_log = saga_log
        self.logger = logging.getLogger(__name__)
    
    async def handle_payment_processed(self, event_data: Dict[str, Any]) -> None:
        """Handle payment processed event"""
        self.logger.info(f"Handling payment processed event: {event_data}")
        
        # Create event object
        event = PaymentProcessed(
            event_id=event_data["event_id"],
            saga_id=event_data["saga_id"],
            order_id=event_data["order_id"],
            payment_id=event_data["payment_id"],
            success=event_data["success"],
            message=event_data["message"],
        )
        
        # Log event in saga
        if event.saga_id:
            await self.saga_log.log_event(event.saga_id, event)
        
        # Get order
        order = await self.order_repository.get_by_id(event.order_id)
        
        if not order:
            self.logger.error(f"Order {event.order_id} not found")
            return
        
        if event.success:
            # Update order status to payment confirmed
            order.update_status(OrderStatus.PAYMENT_CONFIRMED)
            
            # Create inventory requested event
            from domain.events import InventoryRequested
            
            inventory_requested = InventoryRequested(
                order_id=order.id,
                items={item.product_id: item.quantity for item in order.items},
                saga_id=order.saga_id,
            )
            
            # Update order status
            order.update_status(OrderStatus.PENDING_INVENTORY)
            
            # Update order in repository
            await self.order_repository.update(order)
            
            # Publish inventory requested event
            await self.message_publisher.publish(
                event=inventory_requested,
                topic="inventory",
            )
            
            # Log event in saga
            if order.saga_id:
                await self.saga_log.log_event(order.saga_id, inventory_requested)
        else:
            # Payment failed, cancel order
            order.update_status(OrderStatus.FAILED)
            order.metadata["payment_failure_reason"] = event.message
            
            # Update order in repository
            await self.order_repository.update(order)
            
            # End saga as failed
            if order.saga_id:
                await self.saga_log.end_saga(order.saga_id, False)
    
    async def handle_inventory_allocated(self, event_data: Dict[str, Any]) -> None:
        """Handle inventory allocated event"""
        self.logger.info(f"Handling inventory allocated event: {event_data}")
        
        # Create event object
        event = InventoryAllocated(
            event_id=event_data["event_id"],
            saga_id=event_data["saga_id"],
            order_id=event_data["order_id"],
            success=event_data["success"],
            message=event_data["message"],
            allocated_items=event_data["allocated_items"],
        )
        
        # Log event in saga
        if event.saga_id:
            await self.saga_log.log_event(event.saga_id, event)
        
        # Get order
        order = await self.order_repository.get_by_id(event.order_id)
        
        if not order:
            self.logger.error(f"Order {event.order_id} not found")
            return
        
        if event.success:
            # Update order status to inventory confirmed
            order.update_status(OrderStatus.INVENTORY_CONFIRMED)
            
            # Store allocated items in metadata
            order.metadata["allocated_items"] = event.allocated_items
            
            # Update order in repository
            await self.order_repository.update(order)
            
            # Order process completed successfully
            if order.saga_id:
                await self.saga_log.end_saga(order.saga_id, True)
        else:
            # Inventory allocation failed, cancel order
            order.update_status(OrderStatus.FAILED)
            order.metadata["inventory_failure_reason"] = event.message
            
            # Update order in repository
            await self.order_repository.update(order)
            
            # End saga as failed
            if order.saga_id:
                await self.saga_log.end_saga(order.saga_id, False)
    
    async def handle_order_shipped(self, event_data: Dict[str, Any]) -> None:
        """Handle order shipped event"""
        self.logger.info(f"Handling order shipped event: {event_data}")
        
        # Create event object
        event = OrderShipped(
            event_id=event_data["event_id"],
            saga_id=event_data["saga_id"],
            order_id=event_data["order_id"],
            tracking_number=event_data["tracking_number"],
        )
        
        # Get order
        order = await self.order_repository.get_by_id(event.order_id)
        
        if not order:
            self.logger.error(f"Order {event.order_id} not found")
            return
        
        # Update order status to shipped
        order.update_status(OrderStatus.SHIPPED)
        
        # Store tracking number in metadata
        order.metadata["tracking_number"] = event.tracking_number
        
        # Update order in repository
        await self.order_repository.update(order)