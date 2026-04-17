from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class FieldDefinition:
    name: str
    field_type: str
    description: str
    required: bool = True
    default: object | None = None


@dataclass(slots=True)
class PrototypeContext:
    archetype: str
    product_name: str
    product_slug: str
    entity_label_singular: str
    entity_label_plural: str
    entity_collection_path: str
    field_definitions: list[FieldDefinition]
    capabilities: list[str]
    assumptions: list[str]
    constraints: list[str]
    keywords: list[str]


@dataclass(slots=True)
class ApiContract:
    name: str
    method: str
    path: str
    request_schema: str
    response_schema: str


@dataclass(slots=True)
class RequirementArtifact:
    context: PrototypeContext
    prd: str
    feature_breakdown: list[str]
    user_stories: list[str]
    api_contracts: list[ApiContract]
    assumptions: list[str]
    constraints: list[str]
    missing_requirements: list[str]


@dataclass(slots=True)
class DatabaseTable:
    name: str
    columns: list[str]
    notes: str


@dataclass(slots=True)
class ServiceBoundary:
    name: str
    responsibility: str
    dependencies: list[str]


@dataclass(slots=True)
class ArchitectureArtifact:
    summary: str
    folder_structure: list[str]
    database_schema: list[DatabaseTable]
    service_boundaries: list[ServiceBoundary]
    rationale: list[str]


@dataclass(slots=True)
class WorkerExecutionRecord:
    worker_name: str
    owned_paths: list[str]
    generated_files: list[str]
    notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ImplementationArtifact:
    output_dir: Path
    entrypoint: Path
    generated_files: list[Path]
    notes: list[str]
    worker_records: list[WorkerExecutionRecord] = field(default_factory=list)


@dataclass(slots=True)
class TestFailure:
    suite: str
    test_name: str
    message: str
    traceback: str


@dataclass(slots=True)
class TestReport:
    passed: bool
    unit_tests: int
    integration_tests: int
    failures: list[TestFailure]
    raw_output: str


@dataclass(slots=True)
class EvaluationFinding:
    severity: Severity
    title: str
    detail: str
    recommendation: str
    affects_architecture: bool = False


@dataclass(slots=True)
class EvaluationReport:
    code_quality_score: int
    maintainability_score: int
    findings: list[EvaluationFinding]
    scalability_risks: list[str]
    security_concerns: list[str]
    refactoring_opportunities: list[str]
    technical_debt: list[str]
    suggested_roadmap: list[str]


@dataclass(slots=True)
class Milestone:
    name: str
    owner: str
    description: str
    status: TaskStatus = TaskStatus.PENDING


@dataclass(slots=True)
class IterationRecord:
    iteration: int
    trigger: str
    actions: list[str]
    result: str


@dataclass(slots=True)
class BuildSummary:
    status: str
    product_idea: str
    product_name: str
    run_id: str
    total_duration_ms: int
    milestones: list[Milestone]
    iterations: list[IterationRecord]
    test_results_summary: str
    risk_assessment: list[str]
    technical_debt: list[str]
    next_iteration_roadmap: list[str]
    outputs: dict[str, str]
    agent_backends: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class BuildResult:
    run_id: str
    run_dir: Path
    requirements: RequirementArtifact
    architecture: ArchitectureArtifact
    implementation: ImplementationArtifact
    test_report: TestReport
    evaluation: EvaluationReport
    summary: BuildSummary
