from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

from ..utils import ensure_directory, to_jsonable, utc_timestamp


@dataclass(slots=True)
class BuildJob:
    job_id: str
    idea: str
    status: str
    created_at: str
    updated_at: str
    run_id: str | None = None
    events: list[dict[str, object]] = field(default_factory=list)
    result_payload: dict[str, object] | None = None
    error: str | None = None


class JobStore:
    """File-backed job store so demo jobs survive process restarts."""

    def __init__(self, output_root: Path | str) -> None:
        self.jobs_dir = ensure_directory(Path(output_root) / "_jobs")

    def load_jobs(self) -> dict[str, BuildJob]:
        jobs: dict[str, BuildJob] = {}
        for path in sorted(self.jobs_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            job = BuildJob(**payload)
            if job.status in {"queued", "running"}:
                job.status = "failed"
                job.error = job.error or "The demo process restarted before the build finished."
                job.updated_at = utc_timestamp()
                self.save(job)
            jobs[job.job_id] = job
        return jobs

    def save(self, job: BuildJob) -> None:
        target = self.jobs_dir / f"{job.job_id}.json"
        temp = target.with_suffix(".tmp")
        temp.write_text(json.dumps(to_jsonable(job), indent=2), encoding="utf-8")
        temp.replace(target)

