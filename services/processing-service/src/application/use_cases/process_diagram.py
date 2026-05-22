import logging
from dataclasses import dataclass

from ...infrastructure.ai.claude_analyzer import ClaudeAnalyzer
from ...infrastructure.ai.guardrails import InputValidationError, OutputValidationError
from ...infrastructure.http.report_client import ReportServiceClient
from ...infrastructure.http.upload_client import UploadServiceClient

logger = logging.getLogger(__name__)


@dataclass
class ProcessDiagramInput:
    analysis_id: str
    file_path: str
    file_type: str
    file_name: str


class ProcessDiagramUseCase:
    def __init__(
        self,
        analyzer: ClaudeAnalyzer,
        upload_client: UploadServiceClient,
        report_client: ReportServiceClient,
    ) -> None:
        self._analyzer = analyzer
        self._upload_client = upload_client
        self._report_client = report_client

    async def execute(self, input_data: ProcessDiagramInput) -> None:
        analysis_id = input_data.analysis_id
        logger.info("Processing diagram for analysis_id=%s", analysis_id)

        await self._upload_client.set_status(analysis_id, "PROCESSING")

        try:
            report_data = await self._analyzer.analyze(
                file_path=input_data.file_path,
                file_type=input_data.file_type,
            )
        except (InputValidationError, OutputValidationError) as e:
            logger.error("Validation error for %s: %s", analysis_id, e)
            await self._upload_client.set_status(analysis_id, "ERROR", error_message=str(e))
            return
        except Exception as e:
            logger.exception("Unexpected error processing %s: %s", analysis_id, e)
            await self._upload_client.set_status(
                analysis_id, "ERROR", error_message="Internal processing error"
            )
            return

        try:
            await self._report_client.save_report(analysis_id, report_data)
        except Exception as e:
            logger.exception("Failed to persist report for %s: %s", analysis_id, e)
            await self._upload_client.set_status(
                analysis_id, "ERROR", error_message="Failed to persist report"
            )
            return

        await self._upload_client.set_status(analysis_id, "ANALYZED")
        logger.info("Analysis complete for analysis_id=%s", analysis_id)
