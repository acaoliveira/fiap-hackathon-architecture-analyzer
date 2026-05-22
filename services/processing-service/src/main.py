import asyncio
import logging

import aio_pika
import httpx

from .application.use_cases.process_diagram import ProcessDiagramUseCase
from .config import settings
from .infrastructure.ai.claude_analyzer import ClaudeAnalyzer
from .infrastructure.http.report_client import ReportServiceClient
from .infrastructure.http.upload_client import UploadServiceClient
from .infrastructure.messaging.rabbitmq_consumer import RabbitMQConsumer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("processing-service")


async def main() -> None:
    logger.info("Processing Service starting…")

    http_client = httpx.AsyncClient(timeout=60.0)
    upload_client = UploadServiceClient(http_client)
    report_client = ReportServiceClient(http_client)
    analyzer = ClaudeAnalyzer()
    use_case = ProcessDiagramUseCase(analyzer, upload_client, report_client)

    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    consumer = RabbitMQConsumer(connection, use_case)
    await consumer.start()

    logger.info("Processing Service ready — consuming messages")
    try:
        await asyncio.Future()  # run forever
    finally:
        await connection.close()
        await http_client.aclose()
        logger.info("Processing Service stopped")


if __name__ == "__main__":
    asyncio.run(main())
