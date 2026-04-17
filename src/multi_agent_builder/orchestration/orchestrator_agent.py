from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path
import time

from ..evaluation.evaluation_agent import EvaluationAgent
from ..implementation.implementation_agent import ImplementationAgent
from ..models import BuildResult, BuildSummary, IterationRecord, Milestone, Severity, TaskStatus
from ..observability.logger import BuildLogger
from ..planning.architecture_agent import ArchitectureAgent
from ..planning.specification_agent import SpecificationAgent
from ..runtime.agent_backends import AgentBackend
from ..testing.testing_agent import TestingAgent
from ..utils import ensure_directory, slugify, utc_timestamp, write_json, write_text
from .retry import RetryPolicy
from .state import BuildState


class OrchestratorAgent:
    """Coordinates the autonomous planning, build, test, and evaluation loop."""

    def __init__(
        self,
        output_root: Path,
        retry_policy: RetryPolicy | None = None,
        agent_backends: dict[str, AgentBackend] | None = None,
    ) -> None:
        self.output_root = ensure_directory(output_root)
        self.retry_policy = retry_policy or RetryPolicy()
        backends = agent_backends or {}
        self.specification_agent = SpecificationAgent(backends.get("specification"))
        self.architecture_agent = ArchitectureAgent(backends.get("architecture"))
        self.implementation_agent = ImplementationAgent(backends.get("implementation"))
        self.testing_agent = TestingAgent(backends.get("testing"))
        self.evaluation_agent = EvaluationAgent(backends.get("evaluation"))

    def execute(
        self,
        product_idea: str,
        event_listener: Callable[[dict[str, object]], None] | None = None,
    ) -> BuildResult:
        started = time.perf_counter()
        run_id = f"{utc_timestamp().replace(':', '').replace('+00:00', 'Z').replace('-', '')}-{slugify(product_idea)[:30]}"
        run_dir = ensure_directory(self.output_root / run_id)
        artifacts_dir = ensure_directory(run_dir / "artifacts")
        logger = BuildLogger(run_dir, event_listener=event_listener)
        state = BuildState(
            product_idea=product_idea,
            milestones=[
                Milestone("specification", "Specification Agent", "Produce requirements and contracts"),
                Milestone("architecture", "Architecture Agent", "Produce architecture and service boundaries"),
                Milestone("implementation", "Implementation Agent", "Generate the prototype implementation"),
                Milestone("testing", "Testing Agent", "Generate and run validation"),
                Milestone("evaluation", "Evaluation Agent", "Assess risks and maintainability"),
                Milestone("summary", "Orchestrator Agent", "Publish structured build summary"),
            ],
        )

        logger.record(
            "orchestrator",
            "build_started",
            "Autonomous build started",
            metadata={"idea": product_idea, "run_id": run_id},
        )
        requirements = self._timed_stage(
            state,
            logger,
            "specification",
            "specification_agent",
            lambda: self.specification_agent.run(product_idea),
        )
        write_text(artifacts_dir / "requirements.md", self.specification_agent.to_markdown(requirements))
        write_json(artifacts_dir / "requirements.json", requirements)

        architecture = self._timed_stage(
            state,
            logger,
            "architecture",
            "architecture_agent",
            lambda: self.architecture_agent.run(requirements),
        )
        write_text(artifacts_dir / "architecture.md", self.architecture_agent.to_markdown(architecture))
        write_json(artifacts_dir / "architecture.json", architecture)

        test_retries = 0
        architecture_retries = 0
        implementation_feedback: list[str] = []
        iteration_records: list[IterationRecord] = []

        while True:
            state.current_iteration += 1
            iteration = state.current_iteration
            logger.record(
                "orchestrator",
                "iteration_started",
                f"Starting iteration {iteration}",
                metadata={"iteration": iteration, "feedback": implementation_feedback},
            )
            implementation = self._timed_stage(
                state,
                logger,
                "implementation",
                "implementation_agent",
                lambda: self.implementation_agent.run(run_dir, requirements, architecture, implementation_feedback),
            )
            test_report = self._timed_stage(
                state,
                logger,
                "testing",
                "testing_agent",
                lambda: self.testing_agent.run(implementation, requirements),
            )
            write_text(artifacts_dir / "test_results.md", self.testing_agent.to_markdown(test_report))
            write_json(artifacts_dir / "test_results.json", test_report)

            evaluation = self._timed_stage(
                state,
                logger,
                "evaluation",
                "evaluation_agent",
                lambda: self.evaluation_agent.run(implementation, requirements, architecture, test_report),
            )
            write_text(artifacts_dir / "evaluation.md", self.evaluation_agent.to_markdown(evaluation))
            write_json(artifacts_dir / "evaluation.json", evaluation)

            needs_architecture_retry = any(
                finding.affects_architecture and finding.severity in {Severity.HIGH, Severity.CRITICAL}
                for finding in evaluation.findings
            )
            if test_report.passed and not needs_architecture_retry:
                iteration_records.append(
                    IterationRecord(
                        iteration=iteration,
                        trigger="initial-build" if iteration == 1 else "retry",
                        actions=["implementation", "testing", "evaluation"],
                        result="passed",
                    )
                )
                break

            if not test_report.passed and test_retries < self.retry_policy.max_test_retries:
                test_retries += 1
                state.failures += 1
                state.mark("testing", TaskStatus.RETRYING)
                implementation_feedback = [
                    f"{failure.test_name}: {failure.message}" for failure in test_report.failures
                ] or ["Validation failed without structured errors"]
                iteration_records.append(
                    IterationRecord(
                        iteration=iteration,
                        trigger="test-failure",
                        actions=["implementation-regeneration"],
                        result=f"retrying with feedback: {implementation_feedback}",
                    )
                )
                logger.record(
                    "orchestrator",
                    "test_retry",
                    "Retrying implementation after test failure",
                    metadata={"iteration": iteration, "feedback": implementation_feedback},
                )
                continue

            if needs_architecture_retry and architecture_retries < self.retry_policy.max_architecture_retries:
                architecture_retries += 1
                state.failures += 1
                state.mark("architecture", TaskStatus.RETRYING)
                revision_feedback = [finding.recommendation for finding in evaluation.findings if finding.affects_architecture]
                architecture = self.architecture_agent.run(requirements, revision_feedback)
                write_text(artifacts_dir / "architecture.md", self.architecture_agent.to_markdown(architecture))
                write_json(artifacts_dir / "architecture.json", architecture)
                implementation_feedback = revision_feedback
                iteration_records.append(
                    IterationRecord(
                        iteration=iteration,
                        trigger="architecture-risk",
                        actions=["architecture-revision", "implementation-regeneration"],
                        result="retrying after evaluation feedback",
                    )
                )
                logger.record(
                    "orchestrator",
                    "architecture_retry",
                    "Retrying planning layer after evaluation warning",
                    metadata={"iteration": iteration, "feedback": revision_feedback},
                )
                continue

            iteration_records.append(
                IterationRecord(
                    iteration=iteration,
                    trigger="retry-exhausted",
                    actions=["halt"],
                    result="stopped after retries were exhausted",
                )
            )
            break

        total_duration_ms = int((time.perf_counter() - started) * 1000)
        state.mark("summary", TaskStatus.COMPLETED)
        state.finished_at = utc_timestamp()
        summary = BuildSummary(
            status="success" if test_report.passed else "failed",
            product_idea=product_idea,
            product_name=requirements.context.product_name,
            run_id=run_id,
            total_duration_ms=total_duration_ms,
            milestones=state.milestones,
            iterations=iteration_records,
            test_results_summary=f"{test_report.unit_tests} unit tests and {test_report.integration_tests} integration tests",
            risk_assessment=evaluation.scalability_risks + evaluation.security_concerns,
            technical_debt=evaluation.technical_debt,
            next_iteration_roadmap=evaluation.suggested_roadmap,
            outputs={
                "run_dir": str(run_dir),
                "prototype_entrypoint": str(implementation.entrypoint),
                "build_summary": str(artifacts_dir / "build_summary.json"),
                "logs": str(run_dir / "logs" / "events.jsonl"),
            },
            agent_backends={
                "specification": self.specification_agent.backend_name,
                "architecture": self.architecture_agent.backend_name,
                "implementation": self.implementation_agent.backend_name,
                "testing": self.testing_agent.backend_name,
                "evaluation": self.evaluation_agent.backend_name,
            },
        )
        write_text(artifacts_dir / "build_summary.md", self._summary_markdown(summary))
        write_json(artifacts_dir / "build_summary.json", summary)
        logger.write_snapshot("state.json", asdict(summary))
        logger.record(
            "orchestrator",
            "build_completed",
            "Autonomous build finished",
            duration_ms=total_duration_ms,
            metadata={"status": summary.status, "run_id": run_id},
        )
        return BuildResult(
            run_id=run_id,
            run_dir=run_dir,
            requirements=requirements,
            architecture=architecture,
            implementation=implementation,
            test_report=test_report,
            evaluation=evaluation,
            summary=summary,
        )

    def _timed_stage(self, state: BuildState, logger: BuildLogger, milestone: str, agent: str, fn):
        state.mark(milestone, TaskStatus.RUNNING)
        logger.record(agent, "stage_started", f"{milestone} started", metadata={"milestone": milestone})
        started = time.perf_counter()
        try:
            result = fn()
        except Exception as exc:  # pragma: no cover
            state.mark(milestone, TaskStatus.FAILED)
            logger.record(
                agent,
                "stage_failed",
                str(exc),
                metadata={"milestone": milestone},
            )
            raise
        duration_ms = int((time.perf_counter() - started) * 1000)
        state.mark(milestone, TaskStatus.COMPLETED)
        logger.record(
            agent,
            "stage_completed",
            f"{milestone} finished",
            duration_ms=duration_ms,
            metadata={"milestone": milestone},
        )
        return result

    @staticmethod
    def _summary_markdown(summary: BuildSummary) -> str:
        lines = [
            "# Build Summary",
            "",
            f"- Status: `{summary.status}`",
            f"- Product idea: `{summary.product_idea}`",
            f"- Product name: `{summary.product_name}`",
            f"- Run id: `{summary.run_id}`",
            f"- Total duration (ms): `{summary.total_duration_ms}`",
            "",
            "## Milestones",
        ]
        for milestone in summary.milestones:
            lines.append(f"- `{milestone.name}` [{milestone.status.value}] owned by {milestone.owner}")
        lines.extend(["", "## Iterations"])
        for iteration in summary.iterations:
            lines.append(
                f"- Iteration {iteration.iteration}: trigger={iteration.trigger}; actions={', '.join(iteration.actions)}; result={iteration.result}"
            )
        lines.extend(["", "## Risks"])
        for risk in summary.risk_assessment:
            lines.append(f"- {risk}")
        lines.extend(["", "## Technical Debt"])
        for item in summary.technical_debt:
            lines.append(f"- {item}")
        lines.extend(["", "## Next Iteration Roadmap"])
        for item in summary.next_iteration_roadmap:
            lines.append(f"- {item}")
        lines.extend(["", "## Outputs"])
        for key, value in summary.outputs.items():
            lines.append(f"- `{key}`: {value}")
        if summary.agent_backends:
            lines.extend(["", "## Agent Backends"])
            for key, value in summary.agent_backends.items():
                lines.append(f"- `{key}`: {value}")
        return "\n".join(lines).rstrip() + "\n"
