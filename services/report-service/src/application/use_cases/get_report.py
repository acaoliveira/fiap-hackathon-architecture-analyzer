from dataclasses import dataclass
from uuid import UUID

from ...domain.entities.report import Report
from ...domain.repositories.report_repository import ReportRepository


class GetReportUseCase:
    def __init__(self, repository: ReportRepository) -> None:
        self._repository = repository

    async def execute(self, analysis_id: UUID) -> Report | None:
        return await self._repository.find_by_analysis_id(analysis_id)
