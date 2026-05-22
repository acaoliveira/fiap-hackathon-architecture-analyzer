from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.analysis import Analysis, AnalysisStatus


class AnalysisRepository(ABC):
    @abstractmethod
    async def save(self, analysis: Analysis) -> Analysis:
        ...

    @abstractmethod
    async def find_by_id(self, analysis_id: UUID) -> Analysis | None:
        ...

    @abstractmethod
    async def update_status(
        self,
        analysis_id: UUID,
        status: AnalysisStatus,
        error_message: str | None = None,
    ) -> None:
        ...
