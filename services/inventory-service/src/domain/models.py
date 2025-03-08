# services/inventory-service/src/domain/models.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, Any, Optional
import uuid


class InventoryStatus(Enum):
    IN_STOCK = auto()
    LOW_STOCK = auto()
    OUT_OF_STOCK = auto()


@dataclass
class Product:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    sku: str = ""
    price: float = 0.0
    quantity: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def status(self) -> InventoryStatus:
        if self.quantity <= 0:
            return InventoryStatus.OUT_OF_STOCK
        elif self.quantity < 10:  # Example threshold for low stock
            return InventoryStatus.LOW_STOCK
        else:
            return InventoryStatus.IN_STOCK
    
    def update_quantity(self, new_quantity: int) -> None:
        self.quantity = new_quantity
        self.updated_at = datetime.now()
    
    def allocate(self, quantity: int) -> bool:
        """
        Allocate inventory for an order. Returns True if allocation was successful.
        """
        if quantity <= self.quantity:
            self.quantity -= quantity
            self.updated_at = datetime.now()
            return True
        return False
    
    def release(self, quantity: int) -> None:
        """
        Release previously allocated inventory back to stock.
        """
        self.quantity += quantity
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sku": self.sku,
            "price": self.price,
            "quantity": self.quantity,
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        product = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            sku=data.get("sku", ""),
            price=data.get("price", 0.0),
            quantity=data.get("quantity", 0),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat())),
            metadata=data.get("metadata", {}),
        )
        return product
