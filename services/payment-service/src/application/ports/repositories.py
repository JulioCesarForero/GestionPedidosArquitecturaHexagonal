# services/payment-service/src/application/ports/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models import Payment


class PaymentRepository(ABC):
    """Port for payment repository operations"""
    
    @abstractmethod
    async def save(self, payment: Payment) -> None:
        """Save a payment to the repository"""
        pass
    
    @abstractmethod
    async def get_by_id(self, payment_id: str) -> Optional[Payment]:
        """Get a payment by its ID"""
        pass
    
    @abstractmethod
    async def get_by_order_id(self, order_id: str) -> List[Payment]:
        """Get payments for a specific order"""
        pass
    
    @abstractmethod
    async def get_by_customer_id(self, customer_id: str) -> List[Payment]:
        """Get payments for a specific customer"""
        pass
    
    @abstractmethod
    async def update(self, payment: Payment) -> None:
        """Update an existing payment"""
        pass
