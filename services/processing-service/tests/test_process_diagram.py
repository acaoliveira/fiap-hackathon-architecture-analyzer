import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.use_cases.process_diagram import ProcessDiagramInput, ProcessDiagramUseCase
from src.infrastructure.ai.guardrails import InputValidationError, OutputValidationError


VALID_REPORT = {
    "summary": "A microservice system.",
    "components": [{"name": "API GW", "type": "gateway", "description": "Entry"}],
    "architectural_risks": [],
    "recommendations": [],
}


@pytest.fixture
def use_case():
    analyzer = AsyncMock()
    upload_client = AsyncMock()
    report_client = AsyncMock()
    return ProcessDiagramUseCase(analyzer, upload_client, report_client), analyzer, upload_client, report_client


@pytest.mark.asyncio
async def test_successful_processing(use_case):
    uc, analyzer, upload_client, report_client = use_case
    analyzer.analyze.return_value = VALID_REPORT

    await uc.execute(ProcessDiagramInput("id-1", "/path/file.png", "image/png", "file.png"))

    upload_client.set_status.assert_any_call("id-1", "PROCESSING")
    report_client.save_report.assert_called_once_with("id-1", VALID_REPORT)
    upload_client.set_status.assert_called_with("id-1", "ANALYZED")


@pytest.mark.asyncio
async def test_sets_error_on_input_validation_failure(use_case):
    uc, analyzer, upload_client, report_client = use_case
    analyzer.analyze.side_effect = InputValidationError("File not found")

    await uc.execute(ProcessDiagramInput("id-2", "/bad/path.png", "image/png", "file.png"))

    upload_client.set_status.assert_called_with("id-2", "ERROR", error_message="File not found")
    report_client.save_report.assert_not_called()


@pytest.mark.asyncio
async def test_sets_error_on_output_validation_failure(use_case):
    uc, analyzer, upload_client, report_client = use_case
    analyzer.analyze.side_effect = OutputValidationError("not_architecture_diagram")

    await uc.execute(ProcessDiagramInput("id-3", "/path/file.png", "image/png", "file.png"))

    upload_client.set_status.assert_called_with("id-3", "ERROR", error_message="not_architecture_diagram")


@pytest.mark.asyncio
async def test_sets_error_when_report_save_fails(use_case):
    uc, analyzer, upload_client, report_client = use_case
    analyzer.analyze.return_value = VALID_REPORT
    report_client.save_report.side_effect = Exception("DB unavailable")

    await uc.execute(ProcessDiagramInput("id-4", "/path/file.png", "image/png", "file.png"))

    upload_client.set_status.assert_called_with("id-4", "ERROR", error_message="Failed to persist report")
