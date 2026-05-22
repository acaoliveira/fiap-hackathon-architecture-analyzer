import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.application.use_cases.create_analysis import CreateAnalysisInput, CreateAnalysisUseCase
from src.application.use_cases.get_analysis import GetAnalysisUseCase
from src.domain.entities.analysis import Analysis, AnalysisStatus


@pytest.mark.asyncio
async def test_create_analysis_returns_received_status():
    repo = AsyncMock()
    storage = AsyncMock()
    publisher = AsyncMock()

    fake_analysis = Analysis(file_name="diagram.png", file_path="/fake/path", file_type="image/png")
    repo.save.return_value = fake_analysis
    storage.save.return_value = "/shared/uploads/123/diagram.png"

    use_case = CreateAnalysisUseCase(repo, storage, publisher)
    result = await use_case.execute(
        CreateAnalysisInput(
            file_name="diagram.png",
            file_content=b"fake-content",
            file_type="image/png",
        )
    )

    assert result.status == AnalysisStatus.RECEIVED.value
    repo.save.assert_called_once()
    publisher.publish_analysis_created.assert_called_once()


@pytest.mark.asyncio
async def test_get_analysis_returns_none_when_not_found():
    repo = AsyncMock()
    repo.find_by_id.return_value = None

    use_case = GetAnalysisUseCase(repo)
    result = await use_case.execute(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_get_analysis_returns_data_when_found():
    repo = AsyncMock()
    analysis = Analysis(file_name="arch.pdf", file_path="/path/arch.pdf", file_type="application/pdf")
    repo.find_by_id.return_value = analysis

    use_case = GetAnalysisUseCase(repo)
    result = await use_case.execute(analysis.id)

    assert result is not None
    assert result.status == AnalysisStatus.RECEIVED.value
    assert result.file_name == "arch.pdf"


@pytest.mark.asyncio
async def test_analysis_entity_status_transitions():
    analysis = Analysis(file_name="test.png", file_path="/path", file_type="image/png")
    assert analysis.status == AnalysisStatus.RECEIVED

    analysis.mark_processing()
    assert analysis.status == AnalysisStatus.PROCESSING

    analysis.mark_analyzed()
    assert analysis.status == AnalysisStatus.ANALYZED


@pytest.mark.asyncio
async def test_analysis_entity_error_transition():
    analysis = Analysis(file_name="test.png", file_path="/path", file_type="image/png")
    analysis.mark_error("AI service unavailable")
    assert analysis.status == AnalysisStatus.ERROR
    assert analysis.error_message == "AI service unavailable"
