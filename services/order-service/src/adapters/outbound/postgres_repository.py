# services/order-service/src/adapters/outbound/postgres_repository.py
from typing import List, Optional, Dict, Any
import json

import asyncpg
from asyncpg.pool import Pool

from domain.models import Order
from application.ports.repositories import OrderRepository


class PostgresOrderRepository(OrderRepository):
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def save(self, order: Order) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO orders (
                    id, customer_id, status, created_at, modified_at, 
                    saga_id, metadata, total_amount
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                order.id,
                order.customer_id,
                order.status.name,
                order.created_at,
                order.modified_at,
                order.saga_id,
                json.dumps(order.metadata),
                order.total_amount,
            )
            
            # Insert order items
            for item in order.items:
                await conn.execute(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, quantity, unit_price
                    ) VALUES ($1, $2, $3, $4)
                    """,
                    order.id,
                    item.product_id,
                    item.quantity,
                    item.unit_price,
                )
    
    async def get_by_id(self, order_id: str) -> Optional[Order]:
        async with self.pool.acquire() as conn:
            # Get order
            order_row = await conn.fetchrow(
                """
                SELECT 
                    id, customer_id, status, created_at, modified_at, 
                    saga_id, metadata, total_amount
                FROM orders
                WHERE id = $1
                """,
                order_id,
            )
            
            if not order_row:
                return None
            
            # Get order items
            item_rows = await conn.fetch(
                """
                SELECT product_id, quantity, unit_price
                FROM order_items
                WHERE order_id = $1
                """,
                order_id,
            )
            
            # Convert to dictionary
            order_dict = {
                "id": order_row["id"],
                "customer_id": order_row["customer_id"],
                "status": order_row["status"],
                "created_at": order_row["created_at"].isoformat(),
                "modified_at": order_row["modified_at"].isoformat(),
                "saga_id": order_row["saga_id"],
                "metadata": json.loads(order_row["metadata"]),
                "items": [
                    {
                        "product_id": item["product_id"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                    }
                    for item in item_rows
                ],
            }
            
            return Order.from_dict(order_dict)
    
    async def get_by_customer_id(self, customer_id: str) -> List[Order]:
        async with self.pool.acquire() as conn:
            # Get orders for customer
            order_rows = await conn.fetch(
                """
                SELECT 
                    id, customer_id, status, created_at, modified_at, 
                    saga_id, metadata, total_amount
                FROM orders
                WHERE customer_id = $1
                ORDER BY created_at DESC
                """,
                customer_id,
            )
            
            orders = []
            
            for order_row in order_rows:
                order_id = order_row["id"]
                
                # Get order items
                item_rows = await conn.fetch(
                    """
                    SELECT product_id, quantity, unit_price
                    FROM order_items
                    WHERE order_id = $1
                    """,
                    order_id,
                )
                
                # Convert to dictionary
                order_dict = {
                    "id": order_id,
                    "customer_id": order_row["customer_id"],
                    "status": order_row["status"],
                    "created_at": order_row["created_at"].isoformat(),
                    "modified_at": order_row["modified_at"].isoformat(),
                    "saga_id": order_row["saga_id"],
                    "metadata": json.loads(order_row["metadata"]),
                    "items": [
                        {
                            "product_id": item["product_id"],
                            "quantity": item["quantity"],
                            "unit_price": item["unit_price"],
                        }
                        for item in item_rows
                    ],
                }
                
                orders.append(Order.from_dict(order_dict))
            
            return orders
    
    async def update(self, order: Order) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Update order
                await conn.execute(
                    """
                    UPDATE orders
                    SET 
                        customer_id = $1,
                        status = $2,
                        modified_at = $3,
                        saga_id = $4,
                        metadata = $5,
                        total_amount = $6
                    WHERE id = $7
                    """,
                    order.customer_id,
                    order.status.name,
                    order.modified_at,
                    order.saga_id,
                    json.dumps(order.metadata),
                    order.total_amount,
                    order.id,
                )
                
                # Delete existing items
                await conn.execute(
                    """
                    DELETE FROM order_items
                    WHERE order_id = $1
                    """,
                    order.id,
                )
                
                # Insert new items
                for item in order.items:
                    await conn.execute(
                        """
                        INSERT INTO order_items (
                            order_id, product_id, quantity, unit_price
                        ) VALUES ($1, $2, $3, $4)
                        """,
                        order.id,
                        item.product_id,
                        item.quantity,
                        item.unit_price,
                    )
    
    async def delete(self, order_id: str) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # Delete order items
                await conn.execute(
                    """
                    DELETE FROM order_items
                    WHERE order_id = $1
                    """,
                    order_id,
                )
                
                # Delete order
                await conn.execute(
                    """
                    DELETE FROM orders
                    WHERE id = $1
                    """,
                    order_id,
                )
