# services/inventory-service/src/application/commands/allocate_inventory.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

from domain.events import InventoryAllocated
from application.ports.repositories import ProductRepository
from application.ports.message_bus import MessagePublisher


@dataclass
class AllocateInventoryCommand:
    order_id: str
    saga_id: Optional[str]
    items: Dict[str, int]  # product_id -> quantity


class AllocateInventoryHandler:
    def __init__(
        self,
        product_repository: ProductRepository,
        message_publisher: MessagePublisher,
    ):
        self.product_repository = product_repository
        self.message_publisher = message_publisher
    
    async def handle(self, command: AllocateInventoryCommand) -> Dict[str, Any]:
        # Keep track of allocated items
        allocated_items = {}
        failed_items = {}
        
        # Attempt to allocate each product
        for product_id, quantity in command.items.items():
            product = await self.product_repository.get_by_id(product_id)
            
            if not product:
                failed_items[product_id] = f"Product {product_id} not found"
                continue
            
            if product.allocate(quantity):
                # Successfully allocated
                allocated_items[product_id] = quantity
                # Update product in repository
                await self.product_repository.update(product)
            else:
                # Failed to allocate due to insufficient quantity
                failed_items[product_id] = f"Insufficient quantity for product {product_id}"
        
        # Determine overall success
        success = len(failed_items) == 0
        
        # If any allocation failed, release all allocated inventory
        if not success:
            for product_id, quantity in allocated_items.items():
                product = await self.product_repository.get_by_id(product_id)
                if product:
                    product.release(quantity)
                    await self.product_repository.update(product)
        
        # Generate message
        message = "Inventory allocated successfully" if success else "Failed to allocate inventory"
        
        # Create inventory allocated event
        inventory_allocated_event = InventoryAllocated(
            order_id=command.order_id,
            success=success,
            message=message if success else str(failed_items),
            allocated_items=allocated_items if success else {},
            saga_id=command.saga_id,
        )
        
        # Publish event
        await self.message_publisher.publish(
            event=inventory_allocated_event,
            topic="inventory",
        )
        
        return {
            "success": success,
            "order_id": command.order_id,
            "allocated_items": allocated_items,
            "failed_items": failed_items,
            "message": message,
        }
