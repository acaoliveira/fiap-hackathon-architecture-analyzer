from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.analysis import Analysis, AnalysisStatus
from ....domain.repositories.analysis_repository import AnalysisRepository
from ..models import AnalysisModel


def _to_domain(model: AnalysisModel) -> Analysis:
    return Analysis(
        id=model.id,
        file_name=model.file_name,
        file_path=model.file_path,
        file_type=model.file_type,
        status=AnalysisStatus(model.status),
        error_message=model.error_message,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class PgAnalysisRepository(AnalysisRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, analysis: Analysis) -> Analysis:
        model = AnalysisModel(
            id=analysis.id,
            file_name=analysis.file_name,
            file_path=analysis.file_path,
            file_type=analysis.file_type,
            status=analysis.status.value,
            error_message=analysis.error_message,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _to_domain(model)

    async def find_by_id(self, analysis_id: UUID) -> Analysis | None:
        result = await self._session.execute(
            select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def update_status(
        self,
        analysis_id: UUID,
        status: AnalysisStatus,
        error_message: str | None = None,
    ) -> None:
        await self._session.execute(
            update(AnalysisModel)
            .where(AnalysisModel.id == analysis_id)
            .values(status=status.value, error_message=error_message, updated_at=datetime.utcnow())
        )
        await self._session.commit()
