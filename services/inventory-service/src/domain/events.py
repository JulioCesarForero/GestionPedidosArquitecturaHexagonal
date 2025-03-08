# services/inventory-service/src/domain/events.py
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
class InventoryReleased(Event):
    order_id: str = ""
    items: Dict[str, int] = field(default_factory=dict)  # product_id -> quantity
    
    def __post_init__(self):
        self.event_type = "inventory_released"
    
    def to_dict(self) -> Dict[str, Any]:
        event_dict = super().to_dict()
        event_dict.update({
            "order_id": self.order_id,
            "items": self.items,
        })
        return event_dict

