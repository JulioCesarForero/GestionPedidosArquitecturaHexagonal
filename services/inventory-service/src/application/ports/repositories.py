# services/inventory-service/src/application/ports/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models import Product


class ProductRepository(ABC):
    """Port for product repository operations"""
    
    @abstractmethod
    async def save(self, product: Product) -> None:
        """Save a product to the repository"""
        pass
    
    @abstractmethod
    async def get_by_id(self, product_id: str) -> Optional[Product]:
        """Get a product by its ID"""
        pass
    
    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get a product by its SKU"""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[Product]:
        """Get all products"""
        pass
    
    @abstractmethod
    async def update(self, product: Product) -> None:
        """Update an existing product"""
        pass
    
    @abstractmethod
    async def delete(self, product_id: str) -> None:
        """Delete a product by its ID"""
        pass