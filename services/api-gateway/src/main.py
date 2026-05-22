import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("api-gateway")

http_client: httpx.AsyncClient | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=60.0)
    logger.info("API Gateway started")
    yield
    await http_client.aclose()
    logger.info("API Gateway stopped")


app = FastAPI(
    title="FIAP Secure Systems – API Gateway",
    description="Entry point for the architecture diagram analysis system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _proxy(request_fn, *args, **kwargs) -> JSONResponse:
    try:
        response = await request_fn(*args, **kwargs)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except httpx.TimeoutException:
        logger.error("Upstream service timed out")
        raise HTTPException(status_code=504, detail="Upstream service timed out")
    except httpx.ConnectError as e:
        logger.error("Cannot connect to upstream service: %s", e)
        raise HTTPException(status_code=503, detail="Upstream service unavailable")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.post("/api/v1/analyses", status_code=202)
async def create_analysis(file: UploadFile = File(...)):
    """Upload an architecture diagram for analysis (image or PDF)."""
    content = await file.read()
    logger.info("Forwarding upload: %s (%s bytes)", file.filename, len(content))
    return await _proxy(
        http_client.post,
        f"{settings.upload_service_url}/analyses",
        files={"file": (file.filename, content, file.content_type)},
    )


@app.get("/api/v1/analyses/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Query the processing status of an analysis."""
    return await _proxy(
        http_client.get,
        f"{settings.upload_service_url}/analyses/{analysis_id}",
    )


@app.get("/api/v1/analyses/{analysis_id}/report")
async def get_report(analysis_id: str):
    """Retrieve the generated technical report."""
    return await _proxy(
        http_client.get,
        f"{settings.report_service_url}/reports/{analysis_id}",
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
