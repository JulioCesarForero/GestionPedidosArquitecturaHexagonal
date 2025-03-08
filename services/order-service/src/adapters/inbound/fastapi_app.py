# services/order-service/src/adapters/inbound/fastapi_app.py
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field

from application.commands.create_order import CreateOrderCommand, CreateOrderHandler, CreateOrderItemDTO
from application.commands.cancel_order import CancelOrderCommand, CancelOrderHandler
from application.queries.get_order import GetOrderQuery, GetOrderHandler, GetCustomerOrdersQuery, GetCustomerOrdersHandler


# Pydantic models for API requests and responses
class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int
    unit_price: float


class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItemRequest]


class OrderResponse(BaseModel):
    id: str
    customer_id: str
    status: str
    created_at: str
    modified_at: str
    total_amount: float
    items: List[Dict[str, Any]]
    saga_id: Optional[str] = None


class CancelOrderRequest(BaseModel):
    reason: str = Field(..., min_length=1)


class CustomerOrdersResponse(BaseModel):
    customer_id: str
    orders: List[OrderResponse]
    total_orders: int


# Dependency to get handlers
class Handlers:
    def __init__(
        self,
        create_order_handler: CreateOrderHandler,
        cancel_order_handler: CancelOrderHandler,
        get_order_handler: GetOrderHandler,
        get_customer_orders_handler: GetCustomerOrdersHandler,
    ):
        self.create_order_handler = create_order_handler
        self.cancel_order_handler = cancel_order_handler
        self.get_order_handler = get_order_handler
        self.get_customer_orders_handler = get_customer_orders_handler


def create_app(handlers: Handlers) -> FastAPI:
    app = FastAPI(title="Order Service API", version="1.0.0")
    
    @app.post("/orders", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
    async def create_order(request: CreateOrderRequest):
        command = CreateOrderCommand(
            customer_id=request.customer_id,
            items=[
                CreateOrderItemDTO(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                )
                for item in request.items
            ],
        )
        
        try:
            result = await handlers.create_order_handler.handle(command)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    
    @app.get("/orders/{order_id}", response_model=OrderResponse)
    async def get_order(order_id: str, include_saga_history: bool = False):
        query = GetOrderQuery(
            order_id=order_id,
            include_saga_history=include_saga_history,
        )
        
        result = await handlers.get_order_handler.handle(query)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with ID {order_id} not found",
            )
        
        return result
    
    @app.post("/orders/{order_id}/cancel", response_model=Dict[str, Any])
    async def cancel_order(order_id: str, request: CancelOrderRequest):
        command = CancelOrderCommand(
            order_id=order_id,
            reason=request.reason,
        )
        
        try:
            result = await handlers.cancel_order_handler.handle(command)
            
            if not result.get("success", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.get("message", "Failed to cancel order"),
                )
            
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
    
    @app.get("/customers/{customer_id}/orders", response_model=CustomerOrdersResponse)
    async def get_customer_orders(customer_id: str):
        query = GetCustomerOrdersQuery(
            customer_id=customer_id,
        )
        
        result = await handlers.get_customer_orders_handler.handle(query)
        
        return result
    
    return app


