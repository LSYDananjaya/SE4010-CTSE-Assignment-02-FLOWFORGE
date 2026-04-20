from __future__ import annotations

from typing import Literal

from flowforge.models.state import GraphState


def route_after_qa(state: GraphState) -> Literal["complete"]:
    """Return the terminal route after QA."""
    return "complete"
