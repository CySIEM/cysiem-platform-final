"""Kafka event producer with automatic stub mode. If
KAFKA_BOOTSTRAP_SERVERS is unset, publish calls are logged and dropped,
so Layer 3 runs standalone without a broker. Wire in `aiokafka` (or
confluent-kafka) here once Layer 1's Kafka cluster is reachable.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.config import get_settings
from app.core.logging import get_logger
from app.events.schemas import EntityExtractedEvent, IOCMatchedEvent

logger = get_logger("cysiem.layer3.events")


class EventProducer:
    def __init__(self) -> None:
        settings = get_settings()
        self._brokers = settings.kafka_bootstrap_servers
        self._entities_topic = settings.kafka_topic_entities
        self._iocs_topic = settings.kafka_topic_iocs

    @property
    def is_enabled(self) -> bool:
        return bool(self._brokers)

    async def publish_entities(self, entities: List[Dict[str, Any]]) -> None:
        event = EntityExtractedEvent(entities=entities)
        await self._publish(self._entities_topic, event.model_dump(mode="json"))

    async def publish_iocs(self, iocs: List[Dict[str, Any]]) -> None:
        event = IOCMatchedEvent(iocs=iocs)
        await self._publish(self._iocs_topic, event.model_dump(mode="json"))

    async def _publish(self, topic: str, payload: Dict[str, Any]) -> None:
        if not self.is_enabled:
            logger.debug("event.publish.stub", topic=topic, payload=payload)
            return
        # Real producer wiring, e.g.:
        #   from aiokafka import AIOKafkaProducer
        #   producer = AIOKafkaProducer(bootstrap_servers=self._brokers)
        #   await producer.start()
        #   await producer.send_and_wait(topic, json.dumps(payload).encode())
        #   await producer.stop()
        logger.info("event.publish", topic=topic, brokers=self._brokers)


event_producer = EventProducer()
