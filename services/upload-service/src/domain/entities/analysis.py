from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class AnalysisStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    ANALYZED = "ANALYZED"
    ERROR = "ERROR"


@dataclass
class Analysis:
    file_name: str
    file_path: str
    file_type: str
    id: UUID = field(default_factory=uuid4)
    status: AnalysisStatus = AnalysisStatus.RECEIVED
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def mark_processing(self) -> None:
        self.status = AnalysisStatus.PROCESSING
        self.updated_at = datetime.utcnow()

    def mark_analyzed(self) -> None:
        self.status = AnalysisStatus.ANALYZED
        self.updated_at = datetime.utcnow()

    def mark_error(self, message: str) -> None:
        self.status = AnalysisStatus.ERROR
        self.error_message = message
        self.updated_at = datetime.utcnow()
