"""In-memory registry: run_id → compiled graph (needed for HITL resume).

Compiled graphs hold a MemorySaver checkpointer with the interrupted thread
state. Without this registry the resume endpoint has no way to continue the
same graph execution after an interrupt.

This is intentionally in-process only — sufficient for a single-worker
deployment. Upgrade to a persistent checkpointer (e.g. AsyncPostgresSaver)
for multi-worker or restart-resilient HITL.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph

_registry: dict[str, "CompiledStateGraph"] = {}


def register(run_id: str, compiled: "CompiledStateGraph") -> None:
    _registry[run_id] = compiled


def lookup(run_id: str) -> "CompiledStateGraph | None":
    return _registry.get(run_id)


def evict(run_id: str) -> None:
    _registry.pop(run_id, None)
