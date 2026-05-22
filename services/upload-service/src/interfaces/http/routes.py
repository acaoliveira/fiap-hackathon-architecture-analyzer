import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.use_cases.create_analysis import CreateAnalysisInput, CreateAnalysisUseCase
from ...application.use_cases.get_analysis import GetAnalysisUseCase
from ...application.use_cases.update_status import UpdateStatusInput, UpdateStatusUseCase
from ...config import ALLOWED_MIME_TYPES, settings
from ...domain.entities.analysis import AnalysisStatus
from ...infrastructure.database.repositories.pg_analysis_repository import PgAnalysisRepository
from ...infrastructure.messaging.rabbitmq_publisher import RabbitMQPublisher
from ...infrastructure.storage.local_storage import LocalStorage
from .schemas import AnalysisStatusResponse, CreateAnalysisResponse, UpdateStatusRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session() -> AsyncSession:
    raise NotImplementedError("Override via dependency injection")


def get_publisher() -> RabbitMQPublisher:
    raise NotImplementedError("Override via dependency injection")


@router.post("/analyses", response_model=CreateAnalysisResponse, status_code=202)
async def create_analysis(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
    publisher: RabbitMQPublisher = Depends(get_publisher),
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: {sorted(ALLOWED_MIME_TYPES)}",
        )

    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed: {settings.max_file_size_bytes // (1024*1024)} MB",
        )
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    repository = PgAnalysisRepository(session)
    storage = LocalStorage(settings.storage_path)

    use_case = CreateAnalysisUseCase(repository, storage, publisher)
    output = await use_case.execute(
        CreateAnalysisInput(
            file_name=file.filename or "upload",
            file_content=content,
            file_type=file.content_type,
        )
    )
    return CreateAnalysisResponse(analysis_id=output.analysis_id, status=output.status)


@router.get("/analyses/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    repository = PgAnalysisRepository(session)
    use_case = GetAnalysisUseCase(repository)
    result = await use_case.execute(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisStatusResponse(**result.__dict__)


@router.patch("/analyses/{analysis_id}/status", status_code=204)
async def update_analysis_status(
    analysis_id: UUID,
    body: UpdateStatusRequest,
    session: AsyncSession = Depends(get_db_session),
):
    try:
        status = AnalysisStatus(body.status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {body.status}")

    repository = PgAnalysisRepository(session)
    use_case = UpdateStatusUseCase(repository)
    await use_case.execute(
        UpdateStatusInput(
            analysis_id=analysis_id,
            status=status,
            error_message=body.error_message,
        )
    )
