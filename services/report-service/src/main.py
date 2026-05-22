import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import settings
from .infrastructure.database.connection import Base, build_engine, build_session_factory
from .interfaces.http import routes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("report-service")

engine = build_engine(settings.database_url)
session_factory = build_session_factory(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Report Service started")
    yield
    await engine.dispose()
    logger.info("Report Service stopped")


app = FastAPI(
    title="Report Service",
    version="1.0.0",
    lifespan=lifespan,
)


async def get_db_session():
    async with session_factory() as session:
        yield session


app.dependency_overrides[routes.get_db_session] = get_db_session
app.include_router(routes.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "report-service"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
