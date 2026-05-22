import logging
from dataclasses import dataclass
from uuid import UUID

from ...domain.entities.analysis import AnalysisStatus
from ...domain.repositories.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)


@dataclass
class UpdateStatusInput:
    analysis_id: UUID
    status: AnalysisStatus
    error_message: str | None = None


class UpdateStatusUseCase:
    def __init__(self, repository: AnalysisRepository) -> None:
        self._repository = repository

    async def execute(self, input_data: UpdateStatusInput) -> None:
        await self._repository.update_status(
            analysis_id=input_data.analysis_id,
            status=input_data.status,
            error_message=input_data.error_message,
        )
        logger.info("Analysis %s status → %s", input_data.analysis_id, input_data.status)
