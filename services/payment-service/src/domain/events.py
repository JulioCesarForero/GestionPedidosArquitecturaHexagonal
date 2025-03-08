# services/payment-service/src/domain/events.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


@dataclass
class Event:
    """Base class for all domain events"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = field(init=False)
    timestamp: datetime = field(default_factory=datetime.now)
    saga_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "saga_id": self.saga_id,
        }


@dataclass
class PaymentRequested(Event):
    order_id: str = ""
    customer_id: str = ""
    amount: float = 0.0
    
    def __post_init__(self):
        self.event_type = "payment_requested"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "amount": self.amount,
        })
        return event_dict


@dataclass
class PaymentProcessed(Event):
    order_id: str = ""
    payment_id: str = ""
    success: bool = False
    message: str = ""
    
    def __post_init__(self):
        self.event_type = "payment_processed"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "success": self.success,
            "message": self.message,
        })
        return event_dict


@dataclass
class PaymentRefunded(Event):
    order_id: str = ""
    payment_id: str = ""
    amount: float = 0.0
    reason: str = ""
    
    def __post_init__(self):
        self.event_type = "payment_refunded"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "payment_id": self.payment_id,
            "amount": self.amount,
            "reason": self.reason,
        })
        return event_dict

