from __future__ import annotations

from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from flowforge.models.outputs import ArtifactPaths, ContextBundle, IntakeResult, PlanResult, QaResult
from flowforge.models.requests import UserRequest
from flowforge.utils.time import make_run_id


WorkflowStatus = Literal[
    "initialized",
    "intake_completed",
    "context_completed",
    "planning_completed",
    "qa_completed",
    "completed",
    "failed",
]


class WorkflowState(BaseModel):
    """Shared typed state passed across all agents."""

    run_id: str
    request: UserRequest
    intake_result: IntakeResult | None = None
    context_bundle: ContextBundle | None = None
    plan_result: PlanResult | None = None
    qa_result: QaResult | None = None
    artifacts: ArtifactPaths | None = None
    trace_file: str = ""
    workflow_status: WorkflowStatus = "initialized"
    errors: list[str] = Field(default_factory=list)

    @classmethod
    def initial(cls, request: UserRequest) -> "WorkflowState":
        """Create an initial workflow state for a request."""
        return cls(run_id=make_run_id(), request=request)


class GraphState(TypedDict):
    """LangGraph state schema wrapping the typed workflow state."""

    workflow: WorkflowState
