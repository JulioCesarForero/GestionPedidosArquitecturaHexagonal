# services/order-service/src/application/queries/get_order.py
from dataclasses import dataclass
from typing import Dict, Any, Optional

from application.ports.repositories import OrderRepository
from application.ports.message_bus import SagaLog


@dataclass
class GetOrderQuery:
    order_id: str
    include_saga_history: bool = False


class GetOrderHandler:
    def __init__(
        self,
        order_repository: OrderRepository,
        saga_log: SagaLog,
    ):
        self.order_repository = order_repository
        self.saga_log = saga_log
    
    async def handle(self, query: GetOrderQuery) -> Optional[Dict[str, Any]]:
        # Retrieve the order
        order = await self.order_repository.get_by_id(query.order_id)
        
        if not order:
            return None
        
        # Convert order to dictionary
        result = order.to_dict()
        
        # Include saga history if requested and if saga exists
        if query.include_saga_history and order.saga_id:
            saga_events = await self.saga_log.get_saga_events(order.saga_id)
            result["saga_history"] = saga_events
        
        return result


@dataclass
class GetCustomerOrdersQuery:
    customer_id: str


class GetCustomerOrdersHandler:
    def __init__(
        self,
        order_repository: OrderRepository,
    ):
        self.order_repository = order_repository
    
    async def handle(self, query: GetCustomerOrdersQuery) -> Dict[str, Any]:
        # Retrieve all orders for the customer
        orders = await self.order_repository.get_by_customer_id(query.customer_id)
        
        # Convert orders to dictionaries
        result = {
            "customer_id": query.customer_id,
            "orders": [order.to_dict() for order in orders],
            "total_orders": len(orders),
        }
        
        return result