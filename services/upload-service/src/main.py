import logging
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .infrastructure.database.connection import Base, build_engine, build_session_factory
from .infrastructure.messaging.rabbitmq_publisher import RabbitMQPublisher
from .interfaces.http import routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("upload-service")

engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)
rabbitmq_connection: aio_pika.RobustConnection | None = None
publisher: RabbitMQPublisher | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_connection, publisher

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")

    rabbitmq_connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    publisher = RabbitMQPublisher(rabbitmq_connection)
    logger.info("Upload Service started")

    yield

    await rabbitmq_connection.close()
    await engine.dispose()
    logger.info("Upload Service stopped")


app = FastAPI(
    title="Upload & Orchestration Service",
    version="1.0.0",
    lifespan=lifespan,
)


async def get_db_session():
    async with session_factory() as session:
        yield session


async def get_publisher():
    return publisher


app.dependency_overrides[routes.get_db_session] = get_db_session
app.dependency_overrides[routes.get_publisher] = get_publisher

app.include_router(routes.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "upload-service"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
