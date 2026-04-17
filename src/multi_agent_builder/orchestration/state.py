from __future__ import annotations

from dataclasses import dataclass, field

from ..models import Milestone, TaskStatus
from ..utils import utc_timestamp


@dataclass(slots=True)
class BuildState:
    product_idea: str
    milestones: list[Milestone]
    current_iteration: int = 0
    failures: int = 0
    started_at: str = field(default_factory=utc_timestamp)
    finished_at: str | None = None

    def mark(self, milestone_name: str, status: TaskStatus) -> None:
        for milestone in self.milestones:
            if milestone.name == milestone_name:
                milestone.status = status
                return
        raise KeyError(f"Unknown milestone: {milestone_name}")

