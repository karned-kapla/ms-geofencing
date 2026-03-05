import json

from kafka import KafkaProducer

from core.entities import IntrusionEvent


class KafkaPublisher:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._topic = topic
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    def publish(self, event: IntrusionEvent) -> None:
        payload = event.model_dump(mode="json")
        self._producer.send(self._topic, value=payload)
        self._producer.flush()

    def close(self) -> None:
        self._producer.close()

