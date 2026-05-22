import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...application.use_cases.get_report import GetReportUseCase
from ...application.use_cases.save_report import SaveReportInput, SaveReportUseCase
from ...infrastructure.database.repositories.pg_report_repository import PgReportRepository
from .schemas import ReportResponse, SaveReportRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db_session() -> AsyncSession:
    raise NotImplementedError("Override via dependency injection")


@router.post("/reports", status_code=201)
async def save_report(
    body: SaveReportRequest,
    session: AsyncSession = Depends(get_db_session),
):
    repository = PgReportRepository(session)
    use_case = SaveReportUseCase(repository)
    report = await use_case.execute(
        SaveReportInput(
            analysis_id=body.analysis_id,
            summary=body.summary,
            components=body.components,
            architectural_risks=body.architectural_risks,
            recommendations=body.recommendations,
        )
    )
    return {"report_id": str(report.id), "analysis_id": str(report.analysis_id)}


@router.get("/reports/{analysis_id}", response_model=ReportResponse)
async def get_report(
    analysis_id: UUID,
    session: AsyncSession = Depends(get_db_session),
):
    repository = PgReportRepository(session)
    use_case = GetReportUseCase(repository)
    report = await use_case.execute(analysis_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found — analysis may still be in progress")
    return ReportResponse(
        report_id=str(report.id),
        analysis_id=str(report.analysis_id),
        summary=report.summary,
        components=report.components,
        architectural_risks=report.architectural_risks,
        recommendations=report.recommendations,
        created_at=report.created_at.isoformat(),
    )
