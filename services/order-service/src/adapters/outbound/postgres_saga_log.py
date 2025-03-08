# services/order-service/src/adapters/outbound/postgres_saga_log.py
import json
from typing import Dict, Any, List
from datetime import datetime

import asyncpg
from asyncpg.pool import Pool

from domain.events import Event
from application.ports.message_bus import SagaLog


class PostgresSagaLog(SagaLog):
    def __init__(self, pool: Pool):
        self.pool = pool
    
    async def start_saga(self, saga_id: str, order_id: str) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO saga_log (
                    saga_id, order_id, status, started_at
                ) VALUES ($1, $2, $3, $4)
                """,
                saga_id,
                order_id,
                "STARTED",
                datetime.now(),
            )
    
    async def log_event(self, saga_id: str, event: Event) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO saga_events (
                    saga_id, event_id, event_type, event_data, timestamp
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                saga_id,
                event.event_id,
                event.event_type,
                json.dumps(event.to_dict()),
                event.timestamp,
            )
    
    async def end_saga(self, saga_id: str, success: bool) -> None:
        status = "COMPLETED" if success else "FAILED"
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE saga_log
                SET 
                    status = $1,
                    ended_at = $2
                WHERE saga_id = $3
                """,
                status,
                datetime.now(),
                saga_id,
            )
    
    async def get_saga_events(self, saga_id: str) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            # Get saga log
            saga_row = await conn.fetchrow(
                """
                SELECT 
                    saga_id, order_id, status, started_at, ended_at
                FROM saga_log
                WHERE saga_id = $1
                """,
                saga_id,
            )
            
            if not saga_row:
                return []
            
            # Get saga events
            event_rows = await conn.fetch(
                """
                SELECT 
                    event_id, event_type, event_data, timestamp
                FROM saga_events
                WHERE saga_id = $1
                ORDER BY timestamp ASC
                """,
                saga_id,
            )
            
            # Convert to list of dictionaries
            events = []
            
            for event_row in event_rows:
                event_data = json.loads(event_row["event_data"])
                events.append({
                    "event_id": event_row["event_id"],
                    "event_type": event_row["event_type"],
                    "timestamp": event_row["timestamp"].isoformat(),
                    "data": event_data,
                })
            
            # Create saga history
            saga_history = {
                "saga_id": saga_row["saga_id"],
                "order_id": saga_row["order_id"],
                "status": saga_row["status"],
                "started_at": saga_row["started_at"].isoformat(),
                "ended_at": saga_row["ended_at"].isoformat() if saga_row["ended_at"] else None,
                "events": events,
            }
            
            return saga_history