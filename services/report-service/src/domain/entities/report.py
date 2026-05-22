from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class Report:
    analysis_id: UUID
    summary: str
    components: list[dict]
    architectural_risks: list[dict]
    recommendations: list[dict]
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
