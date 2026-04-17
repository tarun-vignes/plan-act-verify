from __future__ import annotations

from ..models import ApiContract, RequirementArtifact
from ..runtime.agent_backends import AgentInvocation, AgentBackend, LLMReadyAgent
from ..utils import bullets
from .heuristics import derive_product_context


class SpecificationAgent(LLMReadyAgent[RequirementArtifact]):
    """Produces the product specification artifact."""

    def __init__(self, backend: AgentBackend | None = None) -> None:
        super().__init__(backend)

    def run(self, product_idea: str) -> RequirementArtifact:
        invocation = AgentInvocation(
            agent_name="Specification Agent",
            role="planning",
            objective="Generate a structured product specification artifact from a high-level idea.",
            inputs={"product_idea": product_idea},
            expected_output="RequirementArtifact",
            constraints=[
                "Preserve a local-first, standard-library-compatible prototype path.",
                "Surface assumptions, constraints, and missing requirements explicitly.",
            ],
        )
        return self.execute_with_backend(invocation, lambda: self._run_heuristic(product_idea))

    def _run_heuristic(self, product_idea: str) -> RequirementArtifact:
        context = derive_product_context(product_idea)
        feature_breakdown = [
            f"Create a new {context.entity_label_singular} through a JSON API.",
            f"List all {context.entity_label_plural} for a lightweight operator view.",
            f"Fetch a single {context.entity_label_singular} by identifier.",
            "Expose metadata so a frontend can render forms without hardcoding fields.",
            "Record build-time assumptions, constraints, and requirement gaps for later iterations.",
        ]
        user_stories = [
            f"As an operator, I can create a {context.entity_label_singular} so I can capture new work without editing code.",
            f"As a team lead, I can review the {context.entity_label_plural} list so I can understand current demand.",
            f"As a downstream client, I can call metadata endpoints so I can generate forms from the contract.",
        ]
        api_contracts = [
            ApiContract(
                name="Health check",
                method="GET",
                path="/health",
                request_schema="No request body.",
                response_schema='{"status": "ok", "product": "<product-name>"}',
            ),
            ApiContract(
                name="Metadata",
                method="GET",
                path="/metadata",
                request_schema="No request body.",
                response_schema='{"product_name": "...", "entity_collection": "...", "fields": [...]}',
            ),
            ApiContract(
                name=f"Create {context.entity_label_singular}",
                method="POST",
                path=f"/{context.entity_collection_path}",
                request_schema=f"JSON object with fields: {', '.join(field.name for field in context.field_definitions)}",
                response_schema='{"id": "...", "record": {...}}',
            ),
            ApiContract(
                name=f"List {context.entity_label_plural}",
                method="GET",
                path=f"/{context.entity_collection_path}",
                request_schema="No request body.",
                response_schema='{"items": [...], "count": 1}',
            ),
            ApiContract(
                name=f"Get {context.entity_label_singular}",
                method="GET",
                path=f"/{context.entity_collection_path}/<id>",
                request_schema="No request body.",
                response_schema='{"item": {...}} or 404 error payload',
            ),
        ]
        assumptions = [
            *context.assumptions,
            "The initial prototype can prioritize traceable architecture over deep domain specialization.",
        ]
        missing_requirements = [
            "Authentication and authorization model",
            "Persistence, retention, and backup expectations",
            "Operational SLAs and expected request volume",
            "Notification, workflow automation, or integration requirements",
        ]
        prd = "\n".join(
            [
                f"# Product Requirements Document: {context.product_name}",
                "",
                "## Intent",
                f"Build a working prototype for the idea: `{product_idea}`.",
                "",
                "## Release Objective",
                f"Deliver a local-first service that lets operators create and review {context.entity_label_plural} while preserving clear architectural seams for later expansion.",
                "",
                "## Scope",
                bullets(feature_breakdown),
                "",
                "## Success Signals",
                "- The service starts locally with no external dependencies.",
                "- Generated tests validate the core create/list/get flows.",
                "- Architecture and build logs remain understandable enough for iterative regeneration.",
                "",
                "## Assumptions",
                bullets(assumptions),
                "",
                "## Constraints",
                bullets(context.constraints),
                "",
                "## Open Questions",
                bullets(missing_requirements),
            ]
        )
        return RequirementArtifact(
            context=context,
            prd=prd,
            feature_breakdown=feature_breakdown,
            user_stories=user_stories,
            api_contracts=api_contracts,
            assumptions=assumptions,
            constraints=context.constraints,
            missing_requirements=missing_requirements,
        )

    @staticmethod
    def to_markdown(requirements: RequirementArtifact) -> str:
        contract_lines = []
        for contract in requirements.api_contracts:
            contract_lines.extend(
                [
                    f"### {contract.name}",
                    f"- Method: `{contract.method}`",
                    f"- Path: `{contract.path}`",
                    f"- Request: {contract.request_schema}",
                    f"- Response: {contract.response_schema}",
                    "",
                ]
            )
        lines = [
            requirements.prd,
            "",
            "## Feature Breakdown",
            bullets(requirements.feature_breakdown),
            "",
            "## User Stories",
            bullets(requirements.user_stories),
            "",
            "## API Contracts",
            *contract_lines,
        ]
        return "\n".join(lines).rstrip() + "\n"
