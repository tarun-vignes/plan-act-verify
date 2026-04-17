from __future__ import annotations

from ..models import (
    ArchitectureArtifact,
    EvaluationFinding,
    EvaluationReport,
    ImplementationArtifact,
    RequirementArtifact,
    Severity,
    TestReport,
)
from ..runtime.agent_backends import AgentInvocation, AgentBackend, LLMReadyAgent
from ..utils import bullets


class EvaluationAgent(LLMReadyAgent[EvaluationReport]):
    """Assesses the generated prototype after validation."""

    def __init__(self, backend: AgentBackend | None = None) -> None:
        super().__init__(backend)

    def run(
        self,
        implementation: ImplementationArtifact,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
        test_report: TestReport,
    ) -> EvaluationReport:
        invocation = AgentInvocation(
            agent_name="Evaluation Agent",
            role="evaluation",
            objective="Assess code quality, maintainability, security, and scalability risks.",
            inputs={
                "prototype_dir": str(implementation.output_dir),
                "tests_passed": test_report.passed,
                "service_boundaries": len(architecture.service_boundaries),
            },
            expected_output="EvaluationReport",
            constraints=[
                "Surface technical debt explicitly.",
                "Flag architecture-affecting issues separately from implementation issues.",
            ],
        )
        return self.execute_with_backend(
            invocation,
            lambda: self._run_heuristic(implementation, requirements, architecture, test_report),
        )

    def _run_heuristic(
        self,
        implementation: ImplementationArtifact,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
        test_report: TestReport,
    ) -> EvaluationReport:
        python_files = list(implementation.output_dir.rglob("*.py"))
        total_lines = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in python_files)
        findings: list[EvaluationFinding] = []
        scalability_risks = [
            "The generated prototype keeps all state in memory, so it will not survive process restarts or scale horizontally.",
            "The synchronous standard-library server is appropriate for a prototype but not for sustained concurrent traffic.",
        ]
        security_concerns = [
            "Authentication and authorization are not implemented in the prototype.",
            "Request payloads are validated for type and presence only; there are no rate limits or abuse controls.",
        ]
        refactoring_opportunities = [
            "Promote the repository boundary to a persistent adapter with migrations.",
            "Introduce versioned API contracts before multiple clients depend on the service.",
            "Move schema definitions into typed objects if the archetype catalog expands substantially.",
        ]
        technical_debt = [
            "Archetype selection is heuristic rather than model-driven, so unusual ideas may map to a generic shape.",
            "The implementation layer generates a single-service prototype, not a distributed production deployment.",
            "The testing layer validates the golden path but does not simulate concurrency or resilience events.",
        ]
        if test_report.passed:
            findings.append(
                EvaluationFinding(
                    severity=Severity.LOW,
                    title="Validation passed",
                    detail="Generated unit and integration suites passed on the first executable design.",
                    recommendation="Keep the current interface contracts stable while the next iteration adds persistence and auth.",
                )
            )
        else:
            findings.append(
                EvaluationFinding(
                    severity=Severity.HIGH,
                    title="Validation failed",
                    detail="The generated prototype did not satisfy its validation suite.",
                    recommendation="Feed the structured failures back into implementation before expanding scope.",
                )
            )
        if any(keyword in {"pci", "hipaa", "gdpr", "compliance"} for keyword in requirements.context.keywords):
            findings.append(
                EvaluationFinding(
                    severity=Severity.HIGH,
                    title="Compliance-sensitive domain",
                    detail="The product idea implies compliance constraints that the prototype does not enforce.",
                    recommendation="Revisit the architecture with audit logging, encryption, data retention, and access policies before shipping.",
                    affects_architecture=True,
                )
            )
        code_quality_score = 70 + (15 if test_report.passed else -20) + (5 if total_lines > 100 else 0)
        maintainability_score = 68 + (10 if len(python_files) >= 7 else 0) + (8 if len(architecture.service_boundaries) >= 4 else 0)
        suggested_roadmap = [
            "Add a persistent repository adapter and schema migrations.",
            "Introduce authentication, authorization, and audit events.",
            "Split evaluation into performance, security, and domain-policy sub-checks.",
            "Add frontend generation or contract-driven client scaffolding on top of the metadata endpoint.",
        ]
        return EvaluationReport(
            code_quality_score=min(code_quality_score, 95),
            maintainability_score=min(maintainability_score, 95),
            findings=findings,
            scalability_risks=scalability_risks,
            security_concerns=security_concerns,
            refactoring_opportunities=refactoring_opportunities,
            technical_debt=technical_debt,
            suggested_roadmap=suggested_roadmap,
        )

    @staticmethod
    def to_markdown(report: EvaluationReport) -> str:
        finding_lines: list[str] = []
        for finding in report.findings:
            finding_lines.extend(
                [
                    f"### {finding.severity.value.upper()}: {finding.title}",
                    f"- Detail: {finding.detail}",
                    f"- Recommendation: {finding.recommendation}",
                    "",
                ]
            )
        lines = [
            "# Evaluation Report",
            "",
            f"- Code quality score: `{report.code_quality_score}`",
            f"- Maintainability score: `{report.maintainability_score}`",
            "",
            "## Findings",
            *finding_lines,
            "## Scalability Risks",
            bullets(report.scalability_risks),
            "",
            "## Security Concerns",
            bullets(report.security_concerns),
            "",
            "## Refactoring Opportunities",
            bullets(report.refactoring_opportunities),
            "",
            "## Technical Debt",
            bullets(report.technical_debt),
            "",
            "## Suggested Roadmap",
            bullets(report.suggested_roadmap),
        ]
        return "\n".join(lines).rstrip() + "\n"
