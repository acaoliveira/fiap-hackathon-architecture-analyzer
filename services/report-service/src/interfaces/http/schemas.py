from pydantic import BaseModel
from uuid import UUID


class SaveReportRequest(BaseModel):
    analysis_id: UUID
    summary: str
    components: list[dict]
    architectural_risks: list[dict]
    recommendations: list[dict]


class ReportResponse(BaseModel):
    report_id: str
    analysis_id: str
    summary: str
    components: list[dict]
    architectural_risks: list[dict]
    recommendations: list[dict]
    created_at: str
