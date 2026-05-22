import logging
from dataclasses import dataclass
from uuid import UUID

from ...domain.entities.report import Report
from ...domain.repositories.report_repository import ReportRepository

logger = logging.getLogger(__name__)


@dataclass
class SaveReportInput:
    analysis_id: UUID
    summary: str
    components: list[dict]
    architectural_risks: list[dict]
    recommendations: list[dict]


class SaveReportUseCase:
    def __init__(self, repository: ReportRepository) -> None:
        self._repository = repository

    async def execute(self, input_data: SaveReportInput) -> Report:
        report = Report(
            analysis_id=input_data.analysis_id,
            summary=input_data.summary,
            components=input_data.components,
            architectural_risks=input_data.architectural_risks,
            recommendations=input_data.recommendations,
        )
        saved = await self._repository.save(report)
        logger.info("Report saved for analysis_id=%s", input_data.analysis_id)
        return saved
