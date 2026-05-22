import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from src.application.use_cases.save_report import SaveReportInput, SaveReportUseCase
from src.application.use_cases.get_report import GetReportUseCase
from src.domain.entities.report import Report


@pytest.mark.asyncio
async def test_save_report_persists_data():
    repo = AsyncMock()
    analysis_id = uuid4()
    report = Report(
        analysis_id=analysis_id,
        summary="Test architecture",
        components=[{"name": "API", "type": "gateway", "description": "Entry"}],
        architectural_risks=[],
        recommendations=[],
    )
    repo.save.return_value = report

    use_case = SaveReportUseCase(repo)
    result = await use_case.execute(
        SaveReportInput(
            analysis_id=analysis_id,
            summary="Test architecture",
            components=[{"name": "API", "type": "gateway", "description": "Entry"}],
            architectural_risks=[],
            recommendations=[],
        )
    )

    repo.save.assert_called_once()
    assert result.analysis_id == analysis_id


@pytest.mark.asyncio
async def test_get_report_returns_none_when_not_found():
    repo = AsyncMock()
    repo.find_by_analysis_id.return_value = None

    use_case = GetReportUseCase(repo)
    result = await use_case.execute(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_report_returns_report_when_found():
    repo = AsyncMock()
    analysis_id = uuid4()
    report = Report(
        analysis_id=analysis_id,
        summary="Microservice system",
        components=[],
        architectural_risks=[],
        recommendations=[],
    )
    repo.find_by_analysis_id.return_value = report

    use_case = GetReportUseCase(repo)
    result = await use_case.execute(analysis_id)
    assert result is not None
    assert result.summary == "Microservice system"
