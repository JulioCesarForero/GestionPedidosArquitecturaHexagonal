# services/order-service/src/application/ports/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models import Order


class OrderRepository(ABC):
    """Port for order repository operations"""
    
    @abstractmethod
    async def save(self, order: Order) -> None:
        """Save an order to the repository"""
        pass
    
    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """Get an order by its ID"""
        pass
    
    @abstractmethod
    async def get_by_customer_id(self, customer_id: str) -> List[Order]:
        """Get all orders for a specific customer"""
        pass
    
    @abstractmethod
    async def update(self, order: Order) -> None:
        """Update an existing order"""
        pass
    
    @abstractmethod
    async def delete(self, order_id: str) -> None:
        """Delete an order by its ID"""
        pass
