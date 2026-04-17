"""
Demo Application for the Multi-Agent Builder.

This module provides a web application that serves a browser-based UI for
interacting with the autonomous prototype builder. Users can submit product
ideas, monitor build progress in real-time, and view generated artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
import threading
import uuid
from urllib.parse import unquote, urlparse

from ..models import BuildSummary
from ..orchestration.orchestrator_agent import OrchestratorAgent
from ..orchestration.retry import RetryPolicy
from ..utils import ensure_directory, to_jsonable, utc_timestamp
from .job_store import BuildJob, JobStore
from .views import render_artifact_page, render_home_page


# List of artifacts that can be viewed in the browser
ALLOWED_ARTIFACTS = {
    "requirements.md",
    "requirements.json",
    "architecture.md",
    "architecture.json",
    "test_results.md",
    "test_results.json",
    "evaluation.md",
    "evaluation.json",
    "build_summary.md",
    "build_summary.json",
}

# Order of milestones for progress tracking
MILESTONE_ORDER = [
    "specification",
    "architecture",
    "implementation",
    "testing",
    "evaluation",
    "summary",
]


class DemoResponse:
    """Simple response object for HTTP responses."""

    def __init__(self, status_code: int, content_type: str, body: bytes) -> None:
        self.status_code = status_code
        self.content_type = content_type
        self.body = body


class DemoApplication:
    """Small web app that exposes the autonomous builder through a browser."""

    def __init__(
        self,
        output_root: Path | str,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.output_root = ensure_directory(Path(output_root))
        self.retry_policy = retry_policy or RetryPolicy()
        self._build_lock = threading.Lock()
        self.job_store = JobStore(self.output_root)
        self._jobs: dict[str, BuildJob] = self.job_store.load_jobs()
        self._jobs_lock = threading.Lock()

    def handle(self, method: str, raw_path: str, body: bytes | None = None) -> DemoResponse:
        parsed = urlparse(raw_path)
        path = unquote(parsed.path)
        if method == "GET" and path in {"/", "/index.html"}:
            return self._html(render_home_page(self._latest_payload()))
        if method == "GET" and path == "/health":
            return self._json({"status": "ok", "service": "demo"})
        if method == "GET" and path == "/api/runs/latest":
            payload = self._latest_payload()
            if payload is None:
                return self._json({"error": "No runs found yet."}, status_code=404)
            return self._json(payload)
        if method == "GET" and path.startswith("/api/runs/"):
            run_id = path.removeprefix("/api/runs/")
            payload = self._payload_for_run(run_id)
            if payload is None:
                return self._json({"error": "Unknown run id."}, status_code=404)
            return self._json(payload)
        if method == "POST" and path == "/api/build":
            return self._handle_build(body or b"{}")
        if method == "GET" and path.startswith("/api/builds/"):
            return self._handle_job_status(path.removeprefix("/api/builds/"))
        if method == "GET" and path.startswith("/runs/"):
            return self._handle_artifact_request(path)
        return self._json({"error": "Route not found"}, status_code=404)

    def _handle_build(self, body: bytes) -> DemoResponse:
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return self._json({"error": "Request body must be valid JSON."}, status_code=400)
        idea = str(payload.get("idea", "")).strip()
        if not idea:
            return self._json({"error": "The idea field is required."}, status_code=400)
        if not self._build_lock.acquire(blocking=False):
            return self._json({"error": "A build is already in progress. Wait for it to finish and retry."}, status_code=409)
        job = BuildJob(
            job_id=str(uuid.uuid4()),
            idea=idea,
            status="queued",
            created_at=utc_timestamp(),
            updated_at=utc_timestamp(),
        )
        with self._jobs_lock:
            self._jobs[job.job_id] = job
            self.job_store.save(job)
        worker = threading.Thread(target=self._run_job, args=(job.job_id,), daemon=True)
        worker.start()
        return self._json(self._job_payload(job.job_id), status_code=202)

    def _run_job(self, job_id: str) -> None:
        self._update_job(job_id, status="running")

        def listener(event: dict[str, object]) -> None:
            self._record_event(job_id, event)

        try:
            with self._jobs_lock:
                job = self._jobs[job_id]
                idea = job.idea
            orchestrator = OrchestratorAgent(self.output_root, self.retry_policy)
            result = orchestrator.execute(idea, event_listener=listener)
            payload = self._payload_from_summary(result.summary)
            self._update_job(
                job_id,
                status="completed",
                run_id=result.run_id,
                result_payload=payload,
            )
        except Exception as exc:  # pragma: no cover - exercised only on unexpected failures
            self._record_event(
                job_id,
                {
                    "timestamp": utc_timestamp(),
                    "agent": "demo",
                    "event": "job_failed",
                    "detail": str(exc),
                    "duration_ms": None,
                    "metadata": {},
                },
            )
            self._update_job(job_id, status="failed", error=str(exc))
        finally:
            self._build_lock.release()

    def _handle_job_status(self, job_id: str) -> DemoResponse:
        payload = self._job_payload(job_id)
        if payload is None:
            return self._json({"error": "Unknown build job."}, status_code=404)
        return self._json(payload)

    def _handle_artifact_request(self, path: str) -> DemoResponse:
        parts = [part for part in path.split("/") if part]
        if len(parts) != 4 or parts[2] != "artifact":
            return self._json({"error": "Invalid artifact route."}, status_code=404)
        run_id, artifact_name = parts[1], parts[3]
        if artifact_name not in ALLOWED_ARTIFACTS:
            return self._json({"error": "Artifact not available."}, status_code=404)
        artifact_path = self.output_root / run_id / "artifacts" / artifact_name
        if not artifact_path.exists():
            return self._json({"error": "Artifact not found."}, status_code=404)
        return self._html(render_artifact_page(run_id, artifact_name, artifact_path.read_text(encoding="utf-8")))

    def _record_event(self, job_id: str, event: dict[str, object]) -> None:
        with self._jobs_lock:
            job = self._jobs[job_id]
            job.events.append(event)
            if len(job.events) > 80:
                job.events = job.events[-80:]
            metadata = event.get("metadata", {})
            if isinstance(metadata, dict) and "run_id" in metadata:
                job.run_id = str(metadata["run_id"])
            job.updated_at = utc_timestamp()
            self.job_store.save(job)

    def _update_job(
        self,
        job_id: str,
        *,
        status: str | None = None,
        run_id: str | None = None,
        result_payload: dict[str, object] | None = None,
        error: str | None = None,
    ) -> None:
        with self._jobs_lock:
            job = self._jobs[job_id]
            if status is not None:
                job.status = status
            if run_id is not None:
                job.run_id = run_id
            if result_payload is not None:
                job.result_payload = result_payload
            if error is not None:
                job.error = error
            job.updated_at = utc_timestamp()
            self.job_store.save(job)

    def _job_payload(self, job_id: str) -> dict[str, object] | None:
        with self._jobs_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            payload = {
                "job": {
                    "job_id": job.job_id,
                    "idea": job.idea,
                    "status": job.status,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at,
                    "run_id": job.run_id,
                    "error": job.error,
                    "events": list(job.events[-20:]),
                    "event_count": len(job.events),
                    "milestones": self._milestones_for_job(job),
                    "current_message": job.events[-1]["detail"] if job.events else "Waiting to start",
                }
            }
            if job.result_payload is not None:
                payload.update(job.result_payload)
            return payload

    def _milestones_for_job(self, job: BuildJob) -> list[dict[str, str]]:
        if job.result_payload is not None and "summary" in job.result_payload:
            summary = job.result_payload["summary"]
            milestones = summary.get("milestones", []) if isinstance(summary, dict) else []
            return [
                {
                    "name": str(item["name"]),
                    "status": str(item["status"]),
                    "owner": str(item["owner"]),
                }
                for item in milestones
            ]
        statuses = {name: "pending" for name in MILESTONE_ORDER}
        for event in job.events:
            event_name = str(event.get("event", ""))
            metadata = event.get("metadata", {})
            milestone = str(metadata.get("milestone", "")) if isinstance(metadata, dict) else ""
            if event_name == "stage_started" and milestone in statuses:
                statuses[milestone] = "running"
            if event_name == "stage_completed" and milestone in statuses:
                statuses[milestone] = "completed"
            if event_name == "stage_failed" and milestone in statuses:
                statuses[milestone] = "failed"
            if event_name == "test_retry":
                statuses["testing"] = "retrying"
                statuses["implementation"] = "retrying"
            if event_name == "architecture_retry":
                statuses["architecture"] = "retrying"
                statuses["implementation"] = "retrying"
        if job.status == "completed":
            statuses["summary"] = "completed"
        if job.status == "failed":
            running = [name for name, status in statuses.items() if status == "running"]
            for name in running:
                statuses[name] = "failed"
        return [{"name": name, "status": statuses[name], "owner": ""} for name in MILESTONE_ORDER]

    def _latest_payload(self) -> dict[str, object] | None:
        candidates = sorted(
            self.output_root.glob("*/artifacts/build_summary.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return None
        return self._payload_for_run(candidates[0].parent.parent.name)

    def _payload_for_run(self, run_id: str) -> dict[str, object] | None:
        summary_path = self.output_root / run_id / "artifacts" / "build_summary.json"
        if not summary_path.exists():
            return None
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        return self._payload_from_summary(summary)

    def _payload_from_summary(self, summary: BuildSummary | dict[str, object]) -> dict[str, object]:
        summary_dict = to_jsonable(summary) if isinstance(summary, BuildSummary) else summary
        run_id = str(summary_dict["run_id"])
        artifact_links = {
            "Requirements": f"/runs/{run_id}/artifact/requirements.md",
            "Architecture": f"/runs/{run_id}/artifact/architecture.md",
            "Tests": f"/runs/{run_id}/artifact/test_results.md",
            "Evaluation": f"/runs/{run_id}/artifact/evaluation.md",
            "Build Summary": f"/runs/{run_id}/artifact/build_summary.md",
        }
        return {
            "summary": summary_dict,
            "artifact_links": artifact_links,
            "api_links": {
                "latest": "/api/runs/latest",
                "run": f"/api/runs/{run_id}",
            },
        }

    @staticmethod
    def _json(payload: dict[str, object], status_code: int = 200) -> DemoResponse:
        return DemoResponse(
            status_code=status_code,
            content_type="application/json; charset=utf-8",
            body=json.dumps(payload).encode("utf-8"),
        )

    @staticmethod
    def _html(content: str, status_code: int = 200) -> DemoResponse:
        return DemoResponse(
            status_code=status_code,
            content_type="text/html; charset=utf-8",
            body=content.encode("utf-8"),
        )
