import json
import logging

import aio_pika

logger = logging.getLogger(__name__)

QUEUE_ANALYSES_CREATED = "analyses.created"


class RabbitMQPublisher:
    def __init__(self, connection: aio_pika.RobustConnection) -> None:
        self._connection = connection
        self._channel: aio_pika.Channel | None = None

    async def _get_channel(self) -> aio_pika.Channel:
        if self._channel is None or self._channel.is_closed:
            self._channel = await self._connection.channel()
            await self._channel.declare_queue(QUEUE_ANALYSES_CREATED, durable=True)
        return self._channel

    async def publish_analysis_created(
        self,
        analysis_id: str,
        file_path: str,
        file_type: str,
        file_name: str,
    ) -> None:
        channel = await self._get_channel()
        payload = {
            "analysis_id": analysis_id,
            "file_path": file_path,
            "file_type": file_type,
            "file_name": file_name,
        }
        message = aio_pika.Message(
            body=json.dumps(payload).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await channel.default_exchange.publish(message, routing_key=QUEUE_ANALYSES_CREATED)
        logger.info("Published analyses.created for analysis_id=%s", analysis_id)
