from __future__ import annotations

from ..models import ImplementationArtifact, RequirementArtifact, TestReport
from ..runtime.agent_backends import AgentInvocation, AgentBackend, LLMReadyAgent
from ..utils import write_text
from .runner import ValidationRunner
from .templates import render_test_files


class TestingAgent(LLMReadyAgent[TestReport]):
    """Generates and executes validation assets."""

    def __init__(self, backend: AgentBackend | None = None) -> None:
        super().__init__(backend)
        self.runner = ValidationRunner()

    def run(
        self,
        implementation: ImplementationArtifact,
        requirements: RequirementArtifact,
    ) -> TestReport:
        invocation = AgentInvocation(
            agent_name="Testing Agent",
            role="verification",
            objective="Generate test assets and validate the prototype implementation.",
            inputs={
                "prototype_dir": str(implementation.output_dir),
                "generated_files": len(implementation.generated_files),
            },
            expected_output="TestReport",
            constraints=[
                "Produce both unit and integration coverage for the generated prototype.",
                "Return structured failure information when validation fails.",
            ],
        )
        return self.execute_with_backend(invocation, lambda: self._run_validation(implementation, requirements))

    def _run_validation(
        self,
        implementation: ImplementationArtifact,
        requirements: RequirementArtifact,
    ) -> TestReport:
        for relative_path, content in render_test_files(requirements).items():
            write_text(implementation.output_dir / relative_path, content)
        return self.runner.run(implementation.output_dir)

    @staticmethod
    def to_markdown(report: TestReport) -> str:
        lines = [
            "# Test Results",
            "",
            f"- Passed: `{report.passed}`",
            f"- Unit tests: `{report.unit_tests}`",
            f"- Integration tests: `{report.integration_tests}`",
        ]
        if report.failures:
            lines.extend(["", "## Failures"])
            for failure in report.failures:
                lines.append(f"- `{failure.suite}.{failure.test_name}`: {failure.message}")
        else:
            lines.extend(["", "## Failures", "- None"])
        lines.extend(["", "## Raw Output", "```text", report.raw_output, "```"])
        return "\n".join(lines).rstrip() + "\n"
