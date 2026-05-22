import logging
from dataclasses import dataclass

from ...domain.entities.analysis import Analysis
from ...domain.repositories.analysis_repository import AnalysisRepository

logger = logging.getLogger(__name__)


@dataclass
class CreateAnalysisInput:
    file_name: str
    file_content: bytes
    file_type: str


@dataclass
class CreateAnalysisOutput:
    analysis_id: str
    status: str


class CreateAnalysisUseCase:
    def __init__(
        self,
        repository: AnalysisRepository,
        storage,
        publisher,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._publisher = publisher

    async def execute(self, input_data: CreateAnalysisInput) -> CreateAnalysisOutput:
        analysis = Analysis(
            file_name=input_data.file_name,
            file_path="",
            file_type=input_data.file_type,
        )

        file_path = await self._storage.save(
            analysis_id=str(analysis.id),
            file_name=input_data.file_name,
            content=input_data.file_content,
        )
        analysis.file_path = file_path

        await self._repository.save(analysis)
        logger.info("Analysis created: %s", analysis.id)

        await self._publisher.publish_analysis_created(
            analysis_id=str(analysis.id),
            file_path=file_path,
            file_type=input_data.file_type,
            file_name=input_data.file_name,
        )

        return CreateAnalysisOutput(
            analysis_id=str(analysis.id),
            status=analysis.status.value,
        )
