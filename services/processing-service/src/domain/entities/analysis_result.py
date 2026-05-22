from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Component:
    name: str
    type: str
    description: str


@dataclass
class ArchitecturalRisk:
    severity: Literal["high", "medium", "low"]
    title: str
    description: str


@dataclass
class Recommendation:
    priority: Literal["high", "medium", "low"]
    title: str
    action: str


@dataclass
class AnalysisResult:
    analysis_id: str
    summary: str
    components: list[Component] = field(default_factory=list)
    architectural_risks: list[ArchitecturalRisk] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
