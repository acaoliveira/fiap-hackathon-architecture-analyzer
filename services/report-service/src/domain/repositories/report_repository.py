from abc import ABC, abstractmethod
from uuid import UUID

from ..entities.report import Report


class ReportRepository(ABC):
    @abstractmethod
    async def save(self, report: Report) -> Report:
        ...

    @abstractmethod
    async def find_by_analysis_id(self, analysis_id: UUID) -> Report | None:
        ...
