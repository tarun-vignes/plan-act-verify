from __future__ import annotations

from pathlib import Path

from ..models import ArchitectureArtifact, ImplementationArtifact, RequirementArtifact
from ..runtime.agent_backends import AgentInvocation, AgentBackend, LLMReadyAgent
from ..utils import ensure_directory, write_text
from .workers import (
    DeliveryWorkerAgent,
    DomainWorkerAgent,
    ParallelWorkerCoordinator,
    SurfaceWorkerAgent,
)


class ImplementationAgent(LLMReadyAgent[ImplementationArtifact]):
    """Generates the working prototype implementation."""

    def __init__(
        self,
        backend: AgentBackend | None = None,
        worker_coordinator: ParallelWorkerCoordinator | None = None,
    ) -> None:
        super().__init__(backend)
        self.worker_coordinator = worker_coordinator or ParallelWorkerCoordinator(
            [
                SurfaceWorkerAgent(),
                DomainWorkerAgent(),
                DeliveryWorkerAgent(),
            ]
        )

    def run(
        self,
        run_dir: Path,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
        feedback: list[str] | None = None,
    ) -> ImplementationArtifact:
        invocation = AgentInvocation(
            agent_name="Implementation Agent",
            role="execution",
            objective="Generate the runnable implementation files that satisfy the architecture artifact.",
            inputs={
                "run_dir": str(run_dir),
                "product_name": requirements.context.product_name,
                "feedback": feedback or [],
            },
            expected_output="ImplementationArtifact",
            constraints=[
                "Preserve modular file boundaries.",
                "Keep worker ownership disjoint so generation can scale in parallel.",
            ],
            notes=[f"parallel_workers={len(self.worker_coordinator.workers)}"],
        )
        return self.execute_with_backend(
            invocation,
            lambda: self._run_parallel(run_dir, requirements, architecture, feedback),
        )

    def _run_parallel(
        self,
        run_dir: Path,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
        feedback: list[str] | None = None,
    ) -> ImplementationArtifact:
        prototype_dir = ensure_directory(run_dir / "prototype")
        rendered, worker_records = self.worker_coordinator.run(requirements, architecture)
        generated_files: list[Path] = []
        for relative_path, content in rendered.items():
            target = prototype_dir / relative_path
            write_text(target, content)
            generated_files.append(target)
        notes = [
            "Rendered a deterministic prototype aligned to the architecture artifact.",
            f"Executed {len(worker_records)} implementation workers in parallel with disjoint ownership.",
            "Kept transport, business logic, repository, and config isolated for later regeneration.",
        ]
        if feedback:
            notes.append(f"Implementation refinement input: {'; '.join(feedback)}")
        return ImplementationArtifact(
            output_dir=prototype_dir,
            entrypoint=prototype_dir / "app" / "server.py",
            generated_files=generated_files,
            notes=notes,
            worker_records=worker_records,
        )
