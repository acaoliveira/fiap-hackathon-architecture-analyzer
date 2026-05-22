from pydantic import BaseModel


class CreateAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str = "Diagram received and queued for analysis"


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    file_name: str
    file_type: str
    error_message: str | None = None
    created_at: str
    updated_at: str


class UpdateStatusRequest(BaseModel):
    status: str
    error_message: str | None = None
