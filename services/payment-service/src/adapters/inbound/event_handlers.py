# services/payment-service/src/adapters/inbound/event_handlers.py
import logging
from typing import Dict, Any

from domain.events import PaymentRequested
from application.commands.process_payment import ProcessPaymentCommand, ProcessPaymentHandler


class EventHandlers:
    def __init__(
        self,
        process_payment_handler: ProcessPaymentHandler,
    ):
        self.process_payment_handler = process_payment_handler
        self.logger = logging.getLogger(__name__)
    
    async def handle_payment_requested(self, event_data: Dict[str, Any]) -> None:
        """Handle payment requested event"""
        self.logger.info(f"Handling payment requested event: {event_data}")
        
        # Create event object
        event = PaymentRequested(
            event_id=event_data["event_id"],
            saga_id=event_data["saga_id"],
            order_id=event_data["order_id"],
            customer_id=event_data["customer_id"],
            amount=event_data["amount"],
        )
        
        # Create process payment command
        command = ProcessPaymentCommand(
            order_id=event.order_id,
            customer_id=event.customer_id,
            amount=event.amount,
            saga_id=event.saga_id,
        )
        
        # Handle command
        await self.process_payment_handler.handle(command)