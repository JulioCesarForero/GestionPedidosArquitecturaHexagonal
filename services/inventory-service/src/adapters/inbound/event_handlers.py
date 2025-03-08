# services/inventory-service/src/adapters/inbound/event_handlers.py
import logging
from typing import Dict, Any

from domain.events import InventoryRequested
from application.commands.allocate_inventory import AllocateInventoryCommand, AllocateInventoryHandler


class EventHandlers:
    def __init__(
        self,
        allocate_inventory_handler: AllocateInventoryHandler,
    ):
        self.allocate_inventory_handler = allocate_inventory_handler
        self.logger = logging.getLogger(__name__)
    
    async def handle_inventory_requested(self, event_data: Dict[str, Any]) -> None:
        """Handle inventory requested event"""
        self.logger.info(f"Handling inventory requested event: {event_data}")
        
        # Create event object
        event = InventoryRequested(
            event_id=event_data["event_id"],
            saga_id=event_data["saga_id"],
            order_id=event_data["order_id"],
            items=event_data["items"],
        )
        
        # Create allocate inventory command
        command = AllocateInventoryCommand(
            order_id=event.order_id,
            saga_id=event.saga_id,
            items=event.items,
        )
        
        # Handle command
        await self.allocate_inventory_handler.handle(command)
