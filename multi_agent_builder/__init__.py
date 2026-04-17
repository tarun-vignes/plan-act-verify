from __future__ import annotations

from pathlib import Path


_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "multi_agent_builder"
__path__ = [str(_SRC_PACKAGE)]

from .orchestration.orchestrator_agent import OrchestratorAgent

__all__ = ["OrchestratorAgent"]

