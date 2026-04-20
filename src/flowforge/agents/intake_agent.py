from __future__ import annotations

from flowforge.agents.prompts import INTAKE_PROMPT
from flowforge.models.outputs import IntakeResult
from flowforge.models.state import WorkflowState
from flowforge.tools.intake_parser import IntakeParserTool
from flowforge.utils.errors import FlowForgeError


class IntakeAgent:
    """Normalize the incoming request before deeper processing."""

    def __init__(self, *, llm_client: object, tool: IntakeParserTool) -> None:
        self.llm_client = llm_client
        self.tool = tool

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run the intake stage and update workflow state."""
        try:
            parsed = self.tool.run(state.request)
            prompt = (
                f"{INTAKE_PROMPT.strip()}\n\n"
                f"Title: {parsed.title}\n"
                f"Type: {parsed.request_type}\n"
                f"Description: {parsed.description}\n"
                f"Constraints: {parsed.constraints}"
            )
            result = self.llm_client.generate_structured(
                prompt=prompt,
                schema=IntakeResult,
                metadata={"agent": "intake", "run_id": state.run_id},
            )
            state.intake_result = result
            state.workflow_status = "intake_completed"
        except Exception as exc:  # noqa: BLE001
            raise FlowForgeError("Intake Agent failed.") from exc
        return state
