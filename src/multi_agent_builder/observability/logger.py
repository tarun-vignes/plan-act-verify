from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

from ..utils import ensure_directory, utc_timestamp, write_json


class BuildLogger:
    """Minimal structured logger for build runs."""

    def __init__(
        self,
        run_dir: Path,
        event_listener: Callable[[dict[str, object]], None] | None = None,
    ) -> None:
        self.log_dir = ensure_directory(run_dir / "logs")
        self.log_file = self.log_dir / "events.jsonl"
        self.event_listener = event_listener

    def record(
        self,
        agent: str,
        event: str,
        detail: str,
        *,
        duration_ms: int | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        payload = {
            "timestamp": utc_timestamp(),
            "agent": agent,
            "event": event,
            "detail": detail,
            "duration_ms": duration_ms,
            "metadata": metadata or {},
        }
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        if self.event_listener is not None:
            self.event_listener(payload)

    def write_snapshot(self, relative_path: str, payload: object) -> None:
        write_json(self.log_dir / relative_path, payload)
