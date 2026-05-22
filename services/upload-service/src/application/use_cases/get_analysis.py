from dataclasses import dataclass
from uuid import UUID

from ...domain.repositories.analysis_repository import AnalysisRepository


@dataclass
class GetAnalysisOutput:
    analysis_id: str
    status: str
    file_name: str
    file_type: str
    error_message: str | None
    created_at: str
    updated_at: str


class GetAnalysisUseCase:
    def __init__(self, repository: AnalysisRepository) -> None:
        self._repository = repository

    async def execute(self, analysis_id: UUID) -> GetAnalysisOutput | None:
        analysis = await self._repository.find_by_id(analysis_id)
        if not analysis:
            return None
        return GetAnalysisOutput(
            analysis_id=str(analysis.id),
            status=analysis.status.value,
            file_name=analysis.file_name,
            file_type=analysis.file_type,
            error_message=analysis.error_message,
            created_at=analysis.created_at.isoformat(),
            updated_at=analysis.updated_at.isoformat(),
        )
