from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.report import Report
from ....domain.repositories.report_repository import ReportRepository
from ..models import ReportModel


def _to_domain(model: ReportModel) -> Report:
    return Report(
        id=model.id,
        analysis_id=model.analysis_id,
        summary=model.summary,
        components=model.components,
        architectural_risks=model.architectural_risks,
        recommendations=model.recommendations,
        created_at=model.created_at,
    )


class PgReportRepository(ReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, report: Report) -> Report:
        model = ReportModel(
            id=report.id,
            analysis_id=report.analysis_id,
            summary=report.summary,
            components=report.components,
            architectural_risks=report.architectural_risks,
            recommendations=report.recommendations,
            created_at=report.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_domain(model)

    async def find_by_analysis_id(self, analysis_id: UUID) -> Report | None:
        result = await self._session.execute(
            select(ReportModel).where(ReportModel.analysis_id == analysis_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None
