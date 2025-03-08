# services/order-service/src/application/ports/message_bus.py
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

from domain.events import Event


class MessagePublisher(ABC):
    """Port for publishing messages/events"""
    
    @abstractmethod
    async def publish(self, event: Event, topic: str) -> None:
        """Publish an event to a specific topic"""
        pass
    
    @abstractmethod
    async def publish_with_key(self, event: Event, topic: str, key: str) -> None:
        """Publish an event to a specific topic with a routing key"""
        pass


class MessageConsumer(ABC):
    """Port for consuming messages/events"""
    
    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Subscribe to a topic with a handler function"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the consumer connection"""
        pass


class SagaLog(ABC):
    """Port for saga transaction logging"""
    
    @abstractmethod
    async def start_saga(self, saga_id: str, order_id: str) -> None:
        """Start a new saga transaction"""
        pass
    
    @abstractmethod
    async def log_event(self, saga_id: str, event: Event) -> None:
        """Log an event in a saga transaction"""
        pass
    
    @abstractmethod
    async def end_saga(self, saga_id: str, success: bool) -> None:
        """End a saga transaction with success or failure"""
        pass
    
    @abstractmethod
    async def get_saga_events(self, saga_id: str) -> List[Dict[str, Any]]:
        """Get all events for a specific saga"""
        pass