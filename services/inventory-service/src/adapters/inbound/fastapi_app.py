# services/inventory-service/src/adapters/inbound/fastapi_app.py
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field

from domain.models import Product, InventoryStatus
from application.commands.allocate_inventory import AllocateInventoryCommand, AllocateInventoryHandler


# Pydantic models for API requests and responses
class ProductRequest(BaseModel):
    name: str
    description: str
    sku: str
    price: float
    quantity: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    sku: str
    price: float
    quantity: int
    status: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class AllocateInventoryRequest(BaseModel):
    order_id: str
    saga_id: Optional[str] = None
    items: Dict[str, int]  # product_id -> quantity


class AllocateInventoryResponse(BaseModel):
    success: bool
    order_id: str
    allocated_items: Dict[str, int]
    failed_items: Dict[str, str]
    message: str


# Dependency to get handlers
class Handlers:
    def __init__(
        self,
        allocate_inventory_handler: AllocateInventoryHandler,
    ):
        self.allocate_inventory_handler = allocate_inventory_handler


def create_app(handlers: Handlers) -> FastAPI:
    app = FastAPI(title="Inventory Service API", version="1.0.0")
    
    @app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
    async def create_product(request: ProductRequest):
        # This would typically call a command handler
        product = Product(
            name=request.name,
            description=request.description,
            sku=request.sku,
            price=request.price,
            quantity=request.quantity,
            metadata=request.metadata,
        )
        
        # For demo purposes, we'll return directly
        return product.to_dict()
    
    @app.post("/inventory/allocate", response_model=AllocateInventoryResponse)
    async def allocate_inventory(request: AllocateInventoryRequest):
        command = AllocateInventoryCommand(
            order_id=request.order_id,
            saga_id=request.saga_id,
            items=request.items,
        )
        
        try:
            result = await handlers.allocate_inventory_handler.handle(command)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    
    return app