from __future__ import annotations

from ..models import ArchitectureArtifact, DatabaseTable, RequirementArtifact, ServiceBoundary
from ..runtime.agent_backends import AgentInvocation, AgentBackend, LLMReadyAgent
from ..utils import bullets


class ArchitectureAgent(LLMReadyAgent[ArchitectureArtifact]):
    """Designs the generated prototype architecture."""

    def __init__(self, backend: AgentBackend | None = None) -> None:
        super().__init__(backend)

    def run(
        self,
        requirements: RequirementArtifact,
        feedback: list[str] | None = None,
    ) -> ArchitectureArtifact:
        invocation = AgentInvocation(
            agent_name="Architecture Agent",
            role="architecture",
            objective="Produce the system architecture, service boundaries, and initial persistence model.",
            inputs={
                "product_name": requirements.context.product_name,
                "entity": requirements.context.entity_label_plural,
                "feedback": feedback or [],
            },
            expected_output="ArchitectureArtifact",
            constraints=[
                "Keep planning and runtime layers modular.",
                "Provide a growth path from prototype storage to production persistence.",
            ],
        )
        return self.execute_with_backend(invocation, lambda: self._run_heuristic(requirements, feedback))

    def _run_heuristic(
        self,
        requirements: RequirementArtifact,
        feedback: list[str] | None = None,
    ) -> ArchitectureArtifact:
        context = requirements.context
        columns = ["id TEXT PRIMARY KEY", "created_at TEXT NOT NULL"]
        for field in context.field_definitions:
            sql_type = "INTEGER" if field.field_type == "int" else "TEXT"
            nullability = "NOT NULL" if field.required and field.default is None else "NULL"
            columns.append(f"{field.name} {sql_type} {nullability}")
        database_schema = [
            DatabaseTable(
                name=context.entity_collection_path.replace("-", "_"),
                columns=columns,
                notes="Prototype uses in-memory storage. This table represents the first production-ready persistence target.",
            )
        ]
        folder_structure = [
            "prototype/app/config.py: product-specific contract and schema definition.",
            "prototype/app/models.py: transport-neutral DTOs and validation exception types.",
            "prototype/app/repository.py: repository abstraction and in-memory adapter.",
            "prototype/app/service.py: business logic and schema-driven validation.",
            "prototype/app/api.py: request routing and response formatting.",
            "prototype/app/server.py: HTTP transport adapter built on BaseHTTPRequestHandler.",
            "prototype/tests/test_service.py: unit coverage for the application layer.",
            "prototype/tests/test_api.py: integration coverage for API and service interaction.",
        ]
        service_boundaries = [
            ServiceBoundary(
                name="HTTP Adapter",
                responsibility="Translate HTTP requests into service calls and format JSON responses.",
                dependencies=["Application Service"],
            ),
            ServiceBoundary(
                name="Application Service",
                responsibility=f"Validate and orchestrate {context.entity_label_singular} operations.",
                dependencies=["Repository Adapter", "Product Config"],
            ),
            ServiceBoundary(
                name="Repository Adapter",
                responsibility="Provide persistence semantics behind a replaceable interface.",
                dependencies=["Domain Models"],
            ),
            ServiceBoundary(
                name="Observability Layer",
                responsibility="Capture structured run events, timing, and artifact locations.",
                dependencies=["Orchestrator"],
            ),
        ]
        rationale = [
            "A layered service keeps planning, orchestration, implementation, testing, and evaluation decoupled.",
            "The prototype stays synchronous and standard-library only so the autonomous loop remains reproducible in CI.",
            "A repository seam keeps the generated application easy to migrate from in-memory storage to SQLite or Postgres.",
            "Metadata endpoints let future frontend or workflow agents discover the contract instead of duplicating schema knowledge.",
        ]
        if feedback:
            rationale.append(f"Architecture revision input: {'; '.join(feedback)}")
        summary = "\n".join(
            [
                f"# Architecture Plan: {context.product_name}",
                "",
                "## Overview",
                f"The prototype is a layered JSON service for managing {context.entity_label_plural}. It uses a standard-library HTTP adapter, a schema-aware service layer, and a replaceable repository boundary.",
                "",
                "## Why This Shape",
                bullets(rationale),
            ]
        )
        return ArchitectureArtifact(
            summary=summary,
            folder_structure=folder_structure,
            database_schema=database_schema,
            service_boundaries=service_boundaries,
            rationale=rationale,
        )

    @staticmethod
    def to_markdown(architecture: ArchitectureArtifact) -> str:
        schema_lines: list[str] = []
        for table in architecture.database_schema:
            schema_lines.extend(
                [
                    f"### Table: `{table.name}`",
                    bullets(table.columns),
                    f"- Notes: {table.notes}",
                    "",
                ]
            )
        boundary_lines: list[str] = []
        for boundary in architecture.service_boundaries:
            boundary_lines.extend(
                [
                    f"### {boundary.name}",
                    f"- Responsibility: {boundary.responsibility}",
                    f"- Dependencies: {', '.join(boundary.dependencies)}",
                    "",
                ]
            )
        lines = [
            architecture.summary,
            "",
            "## Folder Structure",
            bullets(architecture.folder_structure),
            "",
            "## Database Schema",
            *schema_lines,
            "## Service Boundaries",
            *boundary_lines,
            "## Rationale",
            bullets(architecture.rationale),
        ]
        return "\n".join(lines).rstrip() + "\n"
