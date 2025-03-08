# services/payment-service/src/application/commands/process_payment.py
from dataclasses import dataclass
from typing import Dict, Any, Optional
import uuid
import random

from domain.models import Payment, PaymentStatus
from domain.events import PaymentProcessed
from application.ports.repositories import PaymentRepository
from application.ports.message_bus import MessagePublisher
from application.ports.payment_gateway import PaymentGateway


@dataclass
class ProcessPaymentCommand:
    order_id: str
    customer_id: str
    amount: float
    saga_id: Optional[str] = None


class ProcessPaymentHandler:
    def __init__(
        self,
        payment_repository: PaymentRepository,
        message_publisher: MessagePublisher,
        payment_gateway: PaymentGateway,
    ):
        self.payment_repository = payment_repository
        self.message_publisher = message_publisher
        self.payment_gateway = payment_gateway
    
    async def handle(self, command: ProcessPaymentCommand) -> Dict[str, Any]:
        # Create a new payment
        payment = Payment(
            order_id=command.order_id,
            customer_id=command.customer_id,
            amount=command.amount,
            saga_id=command.saga_id,
        )
        
        # Save the payment
        await self.payment_repository.save(payment)
        
        # Process the payment with the payment gateway
        try:
            payment.update_status(PaymentStatus.PROCESSING)
            await self.payment_repository.update(payment)
            
            # Use the payment gateway to process the payment
            payment_result = await self.payment_gateway.process_payment(
                payment_id=payment.id,
                amount=payment.amount,
                customer_id=payment.customer_id,
            )
            
            if payment_result["success"]:
                # Payment successful
                payment.complete(payment_result["transaction_id"])
            else:
                # Payment failed
                payment.fail(payment_result["message"])
            
            # Update the payment
            await self.payment_repository.update(payment)
            
            # Create payment processed event
            payment_processed_event = PaymentProcessed(
                order_id=payment.order_id,
                payment_id=payment.id,
                success=payment.status == PaymentStatus.COMPLETED,
                message=payment_result["message"],
                saga_id=payment.saga_id,
            )
            
            # Publish the event
            await self.message_publisher.publish(
                event=payment_processed_event,
                topic="payments",
            )
            
            return {
                "payment_id": payment.id,
                "status": payment.status.name,
                "success": payment.status == PaymentStatus.COMPLETED,
                "message": payment_result["message"],
            }
        except Exception as e:
            # Handle exception
            payment.fail(str(e))
            await self.payment_repository.update(payment)
            
            # Create payment processed event (failure)
            payment_processed_event = PaymentProcessed(
                order_id=payment.order_id,
                payment_id=payment.id,
                success=False,
                message=f"Payment processing error: {str(e)}",
                saga_id=payment.saga_id,
            )
            
            # Publish the event
            await self.message_publisher.publish(
                event=payment_processed_event,
                topic="payments",
            )
            
            return {
                "payment_id": payment.id,
                "status": payment.status.name,
                "success": False,
                "message": f"Payment processing error: {str(e)}",
            }
