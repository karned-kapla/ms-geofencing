import json
import logging

from kafka import KafkaProducer
from kafka.errors import KafkaError

from core.entities import IntrusionEvent

logger = logging.getLogger(__name__)


class KafkaPublisher:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._producer: KafkaProducer | None = None

    def _connect(self) -> bool:
        try:
            self._producer = KafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                request_timeout_ms=5000,
                api_version_auto_timeout_ms=5000,
            )
            logger.info("Kafka connected to %s", self._bootstrap_servers)
            return True
        except KafkaError as e:
            logger.warning("Kafka unavailable (%s), will retry on next event.", e)
            self._producer = None
            return False

    def publish(self, event: IntrusionEvent) -> None:
        if self._producer is None and not self._connect():
            return
        try:
            payload = event.model_dump(mode="json")
            self._producer.send(self._topic, value=payload)
            self._producer.flush()
        except KafkaError as e:
            logger.warning("Kafka publish failed (%s), resetting connection.", e)
            self._producer = None

    def close(self) -> None:
        if self._producer:
            self._producer.close()
