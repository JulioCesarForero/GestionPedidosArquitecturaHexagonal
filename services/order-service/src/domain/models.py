# services/order-service/src/domain/models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional, Dict, Any
import uuid


class OrderStatus(Enum):
    CREATED = auto()
    PENDING_PAYMENT = auto()
    PAYMENT_CONFIRMED = auto()
    PENDING_INVENTORY = auto()
    INVENTORY_CONFIRMED = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()
    FAILED = auto()


@dataclass
class OrderItem:
    product_id: str
    quantity: int
    unit_price: float
    
    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class Order:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    saga_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_amount(self) -> float:
        return sum(item.total_price for item in self.items)
    
    def add_item(self, product_id: str, quantity: int, unit_price: float) -> None:
        self.items.append(OrderItem(product_id=product_id, quantity=quantity, unit_price=unit_price))
        self.modified_at = datetime.now()
    
    def update_status(self, status: OrderStatus) -> None:
        self.status = status
        self.modified_at = datetime.now()
    
    def cancel(self) -> None:
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError("Cannot cancel an order that has been shipped or delivered")
        self.status = OrderStatus.CANCELLED
        self.modified_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                }
                for item in self.items
            ],
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
            "saga_id": self.saga_id,
            "metadata": self.metadata,
            "total_amount": self.total_amount,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Order":
        items = [
            OrderItem(
                product_id=item["product_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            for item in data.get("items", [])
        ]
        
        order = cls(
            id=data.get("id", str(uuid.uuid4())),
            customer_id=data.get("customer_id", ""),
            items=items,
            status=OrderStatus[data.get("status", OrderStatus.CREATED.name)],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            modified_at=datetime.fromisoformat(data.get("modified_at", datetime.now().isoformat())),
            saga_id=data.get("saga_id"),
            metadata=data.get("metadata", {}),
        )
        
        return order