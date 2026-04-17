from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from ..models import ArchitectureArtifact, RequirementArtifact, WorkerExecutionRecord
from .templates import render_delivery_files, render_domain_files, render_surface_files


@dataclass(slots=True)
class ImplementationWorkerOutput:
    worker_name: str
    files: dict[str, str]
    notes: list[str]


class ImplementationWorkerAgent:
    """Base class for implementation workers that own disjoint file sets."""

    worker_name = "worker"
    owned_paths: tuple[str, ...] = ()

    def run(
        self,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
    ) -> ImplementationWorkerOutput:
        raise NotImplementedError


class SurfaceWorkerAgent(ImplementationWorkerAgent):
    worker_name = "surface-worker"
    owned_paths = ("README.md", "app/__init__.py", "app/config.py")

    def run(
        self,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
    ) -> ImplementationWorkerOutput:
        return ImplementationWorkerOutput(
            worker_name=self.worker_name,
            files=render_surface_files(requirements, architecture),
            notes=["Rendered product-facing docs and static configuration files."],
        )


class DomainWorkerAgent(ImplementationWorkerAgent):
    worker_name = "domain-worker"
    owned_paths = ("app/models.py", "app/repository.py", "app/service.py")

    def run(
        self,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
    ) -> ImplementationWorkerOutput:
        return ImplementationWorkerOutput(
            worker_name=self.worker_name,
            files=render_domain_files(requirements),
            notes=["Rendered core domain and repository files."],
        )


class DeliveryWorkerAgent(ImplementationWorkerAgent):
    worker_name = "delivery-worker"
    owned_paths = ("app/api.py", "app/server.py")

    def run(
        self,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
    ) -> ImplementationWorkerOutput:
        return ImplementationWorkerOutput(
            worker_name=self.worker_name,
            files=render_delivery_files(requirements),
            notes=["Rendered delivery and HTTP adapter files."],
        )


class ParallelWorkerCoordinator:
    """Runs implementation workers concurrently over disjoint write scopes."""

    def __init__(self, workers: list[ImplementationWorkerAgent]) -> None:
        self.workers = workers

    def run(
        self,
        requirements: RequirementArtifact,
        architecture: ArchitectureArtifact,
    ) -> tuple[dict[str, str], list[WorkerExecutionRecord]]:
        rendered_files: dict[str, str] = {}
        worker_records: list[WorkerExecutionRecord] = []
        max_workers = max(1, len(self.workers))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker.run, requirements, architecture) for worker in self.workers]
            for worker, future in zip(self.workers, futures, strict=True):
                output = future.result()
                overlap = set(rendered_files).intersection(output.files)
                if overlap:
                    raise ValueError(f"Worker {worker.worker_name} produced overlapping files: {sorted(overlap)}")
                rendered_files.update(output.files)
                worker_records.append(
                    WorkerExecutionRecord(
                        worker_name=output.worker_name,
                        owned_paths=list(worker.owned_paths),
                        generated_files=sorted(output.files.keys()),
                        notes=output.notes,
                    )
                )
        return rendered_files, worker_records

