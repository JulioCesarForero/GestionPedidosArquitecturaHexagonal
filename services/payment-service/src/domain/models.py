# services/payment-service/src/domain/models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional
import uuid


class PaymentStatus(Enum):
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    REFUNDED = auto()


class PaymentMethod(Enum):
    CREDIT_CARD = auto()
    DEBIT_CARD = auto()
    PAYPAL = auto()
    BANK_TRANSFER = auto()
    CRYPTOCURRENCY = auto()


@dataclass
class Payment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    customer_id: str = ""
    amount: float = 0.0
    currency: str = "USD"
    status: PaymentStatus = PaymentStatus.PENDING
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    transaction_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    saga_id: Optional[str] = None
    
    def update_status(self, status: PaymentStatus) -> None:
        self.status = status
        self.updated_at = datetime.now()
    
    def complete(self, transaction_id: str) -> None:
        self.transaction_id = transaction_id
        self.status = PaymentStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def fail(self, reason: str) -> None:
        self.status = PaymentStatus.FAILED
        self.metadata["failure_reason"] = reason
        self.updated_at = datetime.now()
    
    def refund(self, reason: str = "") -> None:
        if self.status != PaymentStatus.COMPLETED:
            raise ValueError("Can only refund completed payments")
        
        self.status = PaymentStatus.REFUNDED
        if reason:
            self.metadata["refund_reason"] = reason
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.name,
            "payment_method": self.payment_method.name,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "saga_id": self.saga_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Payment":
        payment = cls(
            id=data.get("id", str(uuid.uuid4())),
            order_id=data.get("order_id", ""),
            customer_id=data.get("customer_id", ""),
            amount=data.get("amount", 0.0),
            currency=data.get("currency", "USD"),
            status=PaymentStatus[data.get("status", PaymentStatus.PENDING.name)],
            payment_method=PaymentMethod[data.get("payment_method", PaymentMethod.CREDIT_CARD.name)],
            transaction_id=data.get("transaction_id"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            metadata=data.get("metadata", {}),
            saga_id=data.get("saga_id"),
        )
        return payment
