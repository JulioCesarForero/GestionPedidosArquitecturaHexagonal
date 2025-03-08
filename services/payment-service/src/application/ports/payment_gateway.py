# services/payment-service/src/application/ports/payment_gateway.py
from abc import ABC, abstractmethod
from typing import Dict, Any


class PaymentGateway(ABC):
    """Port for payment gateway operations"""
    
    @abstractmethod
    async def process_payment(
        self, payment_id: str, amount: float, customer_id: str
    ) -> Dict[str, Any]:
        """
        Process a payment through the payment gateway
        
        Returns a dictionary with:
        - success: bool
        - transaction_id: str (if success is True)
        - message: str
        """
        pass
    
    @abstractmethod
    async def refund_payment(
        self, transaction_id: str, amount: float, reason: str = ""
    ) -> Dict[str, Any]:
        """
        Refund a payment through the payment gateway
        
        Returns a dictionary with:
        - success: bool
        - refund_id: str (if success is True)
        - message: str
        """
        pass
