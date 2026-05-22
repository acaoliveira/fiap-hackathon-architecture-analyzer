import json
import logging

import aio_pika

from ...application.use_cases.process_diagram import ProcessDiagramInput, ProcessDiagramUseCase

logger = logging.getLogger(__name__)

QUEUE_ANALYSES_CREATED = "analyses.created"


class RabbitMQConsumer:
    def __init__(self, connection: aio_pika.RobustConnection, use_case: ProcessDiagramUseCase) -> None:
        self._connection = connection
        self._use_case = use_case

    async def start(self) -> None:
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue(QUEUE_ANALYSES_CREATED, durable=True)
        logger.info("Waiting for messages on queue: %s", QUEUE_ANALYSES_CREATED)
        await queue.consume(self._handle_message)

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        async with message.process(requeue=False):
            try:
                payload = json.loads(message.body.decode())
                logger.info("Received message: analysis_id=%s", payload.get("analysis_id"))

                await self._use_case.execute(
                    ProcessDiagramInput(
                        analysis_id=payload["analysis_id"],
                        file_path=payload["file_path"],
                        file_type=payload["file_type"],
                        file_name=payload["file_name"],
                    )
                )
            except (KeyError, json.JSONDecodeError) as e:
                logger.error("Malformed message: %s — body: %s", e, message.body[:200])
            except Exception as e:
                logger.exception("Error handling message: %s", e)
