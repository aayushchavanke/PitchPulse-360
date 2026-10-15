"""
PitchPulse 360 - Live Event Streaming (Kafka / Redpanda Pattern) (CO3 & Lab 10)
Provides:
- Event Producer: Generates high-velocity match events (shots, passes, fouls)
- Event Consumer: Reads streaming messages, validates format, routes bad messages to DLQ
- Compatible with Apache Kafka / Redpanda and includes an embedded streaming broker
"""

import time
import json
import queue
import threading
from typing import Dict, Any, Callable, Optional
from streaming.dead_letter_queue import DeadLetterQueue

class EmbeddedKafkaBroker:
    """Thread-safe embedded message broker implementing Pub/Sub semantics."""
    def __init__(self):
        self.topics: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()

    def get_topic_queue(self, topic: str) -> queue.Queue:
        with self.lock:
            if topic not in self.topics:
                self.topics[topic] = queue.Queue()
            return self.topics[topic]

    def produce(self, topic: str, message: Dict[str, Any]) -> None:
        q = self.get_topic_queue(topic)
        q.put(message)

    def consume(self, topic: str, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        q = self.get_topic_queue(topic)
        try:
            return q.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

GLOBAL_BROKER = EmbeddedKafkaBroker()

class FootballEventProducer:
    def __init__(self, topic: str = "football-live-events"):
        self.topic = topic
        self.broker = GLOBAL_BROKER

    def publish_event(self, event_payload: Dict[str, Any]) -> None:
        """Publishes an event to the Kafka topic."""
        self.broker.produce(self.topic, event_payload)

class FootballEventConsumer:
    def __init__(self, topic: str = "football-live-events"):
        self.topic = topic
        self.broker = GLOBAL_BROKER
        self.dlq = DeadLetterQueue()

    def process_stream(self, max_events: int = 50, on_event_callback: Optional[Callable] = None) -> Dict[str, int]:
        """
        Consumes events from topic.
        Validates schema, routes corrupted records to DLQ, and passes valid events downstream.
        """
        consumed = 0
        valid_count = 0
        quarantined_count = 0

        while consumed < max_events:
            msg = self.broker.consume(self.topic, timeout=0.2)
            if msg is None:
                break
            consumed += 1

            # Ingestion Validation / Quality Rule
            is_valid, reason = self._validate_payload(msg)
            if not is_valid:
                self.dlq.route_to_dlq(msg, error_reason=reason, source="KafkaConsumer")
                quarantined_count += 1
            else:
                valid_count += 1
                if on_event_callback:
                    on_event_callback(msg)

        return {
            "consumed": consumed,
            "valid": valid_count,
            "quarantined_to_dlq": quarantined_count
        }

    def _validate_payload(self, msg: Any) -> (bool, str):
        if not isinstance(msg, dict):
            return False, "Payload must be a JSON dictionary"
        if "id" not in msg or not msg["id"]:
            return False, "Missing required 'id' attribute"
        if "team" not in msg:
            return False, "Missing 'team' attribute"
        return True, "Valid"

if __name__ == "__main__":
    producer = FootballEventProducer()
    consumer = FootballEventConsumer()

    producer.publish_event({"id": "evt-101", "team": "Argentina", "minute": 12, "type": {"name": "Pass"}})
    producer.publish_event({"broken": "data"}) # should go to DLQ

    results = consumer.process_stream(max_events=5)
    print("Stream test results:", results)
