from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RetryPolicy:
    max_test_retries: int = 2
    max_architecture_retries: int = 1

