from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Protocol, TypeVar


T = TypeVar("T")


@dataclass(slots=True)
class AgentInvocation:
    agent_name: str
    role: str
    objective: str
    inputs: dict[str, Any]
    expected_output: str
    constraints: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class AgentBackend(Protocol):
    backend_name: str

    def execute(self, invocation: AgentInvocation, fallback: Callable[[], T]) -> T:
        """Run the agent invocation, optionally delegating to an LLM-backed implementation."""


class HeuristicAgentBackend:
    """Default backend that uses the local deterministic implementation."""

    backend_name = "heuristic"

    def execute(self, invocation: AgentInvocation, fallback: Callable[[], T]) -> T:
        return fallback()


class RecordingLLMBackend:
    """
    LLM-ready stub backend.

    This does not call a model, but it captures structured invocations so the system can be
    wired to a real model backend later without changing the agent interfaces.
    """

    backend_name = "recording-llm"

    def __init__(self) -> None:
        self.invocations: list[AgentInvocation] = []

    def execute(self, invocation: AgentInvocation, fallback: Callable[[], T]) -> T:
        self.invocations.append(invocation)
        return fallback()


class LLMReadyAgent(Generic[T]):
    """Shared helper for agents that can swap deterministic and LLM-backed backends."""

    def __init__(self, backend: AgentBackend | None = None) -> None:
        self.backend = backend or HeuristicAgentBackend()

    @property
    def backend_name(self) -> str:
        return getattr(self.backend, "backend_name", self.backend.__class__.__name__)

    def execute_with_backend(self, invocation: AgentInvocation, fallback: Callable[[], T]) -> T:
        return self.backend.execute(invocation, fallback)

