# services/payment-service/src/adapters/outbound/mock_payment_gateway.py
import asyncio
import random
import uuid
from typing import Dict, Any

from application.ports.payment_gateway import PaymentGateway


class MockPaymentGateway(PaymentGateway):
    """
    A mock implementation of a payment gateway for testing purposes.
    In a real application, this would integrate with an actual payment processor.
    """
    
    async def process_payment(
        self, payment_id: str, amount: float, customer_id: str
    ) -> Dict[str, Any]:
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        # Simulate payment processing
        success_rate = 0.9  # 90% success rate
        success = random.random() < success_rate
        
        if success:
            return {
                "success": True,
                "transaction_id": f"txn-{uuid.uuid4()}",
                "message": "Payment processed successfully",
            }
        else:
            # Simulate various failure scenarios
            failure_reasons = [
                "Insufficient funds",
                "Card declined",
                "Payment method not supported",
                "Gateway timeout",
                "Invalid card details",
            ]
            
            return {
                "success": False,
                "transaction_id": None,
                "message": random.choice(failure_reasons),
            }
    
    async def refund_payment(
        self, transaction_id: str, amount: float, reason: str = ""
    ) -> Dict[str, Any]:
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        # Simulate refund processing
        success_rate = 0.95  # 95% success rate for refunds
        success = random.random() < success_rate
        
        if success:
            return {
                "success": True,
                "refund_id": f"ref-{uuid.uuid4()}",
                "message": "Refund processed successfully",
            }
        else:
            return {
                "success": False,
                "refund_id": None,
                "message": "Failed to process refund: Transaction not found or already refunded",
            }

