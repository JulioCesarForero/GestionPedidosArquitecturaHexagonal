# services/order-service/src/domain/events.py
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
class OrderCreated(Event):
    order_id: str = ""
    customer_id: str = ""
    total_amount: float = 0.0
    items: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        self.event_type = "order_created"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "total_amount": self.total_amount,
            "items": self.items,
        })
        return event_dict


@dataclass
class OrderCancelled(Event):
    order_id: str = ""
    reason: str = ""
    
    def __post_init__(self):
        self.event_type = "order_cancelled"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "reason": self.reason,
        })
        return event_dict


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
class InventoryRequested(Event):
    order_id: str = ""
    items: Dict[str, int] = field(default_factory=dict)  # product_id -> quantity
    
    def __post_init__(self):
        self.event_type = "inventory_requested"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "items": self.items,
        })
        return event_dict


@dataclass
class InventoryAllocated(Event):
    order_id: str = ""
    success: bool = False
    message: str = ""
    allocated_items: Dict[str, int] = field(default_factory=dict)  # product_id -> quantity
    
    def __post_init__(self):
        self.event_type = "inventory_allocated"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "success": self.success,
            "message": self.message,
            "allocated_items": self.allocated_items,
        })
        return event_dict


@dataclass
class OrderShipped(Event):
    order_id: str = ""
    tracking_number: str = ""
    
    def __post_init__(self):
        self.event_type = "order_shipped"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "tracking_number": self.tracking_number,
        })
        return event_dict