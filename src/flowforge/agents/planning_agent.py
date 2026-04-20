from __future__ import annotations

from flowforge.agents.prompts import PLANNING_PROMPT
from flowforge.models.outputs import PlanResult
from flowforge.models.state import WorkflowState
from flowforge.tools.task_plan_builder import TaskPlanBuilderTool
from flowforge.utils.errors import FlowForgeError


class PlanningAgent:
    """Generate an implementation-ready task plan."""

    def __init__(self, *, llm_client: object, tool: TaskPlanBuilderTool) -> None:
        self.llm_client = llm_client
        self.tool = tool

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run planning and normalize the resulting task graph."""
        if state.intake_result is None or state.context_bundle is None:
            raise FlowForgeError("Planning Agent requires intake and context outputs.")

        try:
            snippets = "\n\n".join(
                f"Path: {snippet.path}\nReason: {snippet.reason}\nContent:\n{snippet.content}"
                for snippet in state.context_bundle.selected_snippets
            )
            prompt = (
                f"{PLANNING_PROMPT.strip()}\n\n"
                f"Request category: {state.intake_result.category}\n"
                f"Expected planning emphasis: {self._planning_emphasis(state.intake_result.category)}\n"
                f"Request summary: {state.intake_result.summary}\n"
                f"Goals: {state.intake_result.goals}\n"
                f"Constraints: {state.context_bundle.constraints or state.request.constraints}\n"
                f"Relevant snippets:\n{snippets}"
            )
            raw_plan = self.llm_client.generate_structured(
                prompt=prompt,
                schema=PlanResult,
                metadata={"agent": "planning", "run_id": state.run_id},
            )
            state.plan_result = self.tool.run(raw_plan)
            state.workflow_status = "planning_completed"
        except Exception as exc:  # noqa: BLE001
            raise FlowForgeError(f"Planning Agent failed: {exc}") from exc
        return state

    @staticmethod
    def _planning_emphasis(category: str) -> str:
        if category == "bug":
            return "reproduction, root cause, fix sequencing, regression risk, and validation"
        return "requirements coverage, design and implementation steps, UX/API impact, edge cases, and rollout"
