# services/order-service/src/adapters/outbound/pulsar_event_publisher.py
import json
import logging
from typing import Any, Dict

import pulsar
from pulsar.schema import AvroSchema

from domain.events import Event
from application.ports.message_bus import MessagePublisher, MessageConsumer


class PulsarMessagePublisher(MessagePublisher):
    def __init__(self, client: pulsar.Client):
        self.client = client
        self.producers = {}
        self.logger = logging.getLogger(__name__)
    
    async def publish(self, event: Event, topic: str) -> None:
        # Get or create producer for the topic
        if topic not in self.producers:
            self.producers[topic] = self.client.create_producer(
                topic=f"persistent://public/default/{topic}",
                schema=AvroSchema(Event)
            )
        
        producer = self.producers[topic]
        
        # Convert event to dictionary
        event_dict = event.to_dict()
        
        try:
            # Publish the event
            producer.send(
                content=json.dumps(event_dict).encode("utf-8"),
                properties={"event_type": event.event_type}
            )
            
            self.logger.info(f"Published event {event.event_id} to topic {topic}")
        except Exception as e:
            self.logger.error(f"Failed to publish event to topic {topic}: {str(e)}")
            raise
    
    async def publish_with_key(self, event: Event, topic: str, key: str) -> None:
        # Get or create producer for the topic
        if topic not in self.producers:
            self.producers[topic] = self.client.create_producer(
                topic=f"persistent://public/default/{topic}",
                schema=AvroSchema(Event)
            )
        
        producer = self.producers[topic]
        
        # Convert event to dictionary
        event_dict = event.to_dict()
        
        try:
            # Publish the event with a key
            producer.send(
                content=json.dumps(event_dict).encode("utf-8"),
                partition_key=key,
                properties={"event_type": event.event_type}
            )
            
            self.logger.info(f"Published event {event.event_id} to topic {topic} with key {key}")
        except Exception as e:
            self.logger.error(f"Failed to publish event to topic {topic} with key {key}: {str(e)}")
            raise


class PulsarMessageConsumer(MessageConsumer):
    def __init__(self, client: pulsar.Client, subscription_name: str):
        self.client = client
        self.subscription_name = subscription_name
        self.consumers = {}
        self.logger = logging.getLogger(__name__)
    
    async def subscribe(self, topic: str, handler: callable) -> None:
        # Create consumer for the topic
        consumer = self.client.subscribe(
            topic=f"persistent://public/default/{topic}",
            subscription_name=self.subscription_name,
            schema=AvroSchema(Event)
        )
        
        # Store consumer
        self.consumers[topic] = consumer
        
        # Start consuming messages
        self.logger.info(f"Subscribed to topic {topic}")
        
        # Start a background task to consume messages
        import asyncio
        asyncio.create_task(self._consume(consumer, handler))
    
    async def _consume(self, consumer: pulsar.Consumer, handler: callable) -> None:
        while True:
            try:
                # Receive message
                msg = consumer.receive()
                
                # Parse message content
                content = json.loads(msg.value().decode("utf-8"))
                
                # Handle message
                await handler(content)
                
                # Acknowledge message
                consumer.acknowledge(msg)
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                # Negative acknowledge message to reprocess it
                consumer.negative_acknowledge(msg)
    
    async def close(self) -> None:
        for topic, consumer in self.consumers.items():
            consumer.close()
        
        self.client.close()