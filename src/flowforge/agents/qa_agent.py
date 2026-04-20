from __future__ import annotations

from flowforge.agents.prompts import QA_PROMPT
from flowforge.models.outputs import QaResult
from flowforge.models.state import WorkflowState
from flowforge.tools.qa_validator import QaValidatorTool
from flowforge.utils.errors import FlowForgeError


class QAAgent:
    """Validate the generated plan before finalization."""

    def __init__(self, *, llm_client: object, tool: QaValidatorTool) -> None:
        self.llm_client = llm_client
        self.tool = tool

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run the QA validation stage."""
        if state.intake_result is None or state.context_bundle is None or state.plan_result is None:
            raise FlowForgeError("QA Agent requires intake, context, and planning outputs.")

        try:
            deterministic_findings = self.tool.run(
                intake=state.intake_result,
                context=state.context_bundle,
                plan=state.plan_result,
            )
            prompt = (
                f"{QA_PROMPT.strip()}\n\n"
                f"Request category: {state.intake_result.category}\n"
                f"Expected QA emphasis: {self._qa_emphasis(state.intake_result.category)}\n"
                f"Deterministic findings: {deterministic_findings}\n"
                f"Plan summary: {state.plan_result.summary}\n"
                f"Task count: {len(state.plan_result.tasks)}\n"
                f"Overall risks: {state.plan_result.overall_risks}"
            )
            result = self.llm_client.generate_structured(
                prompt=prompt,
                schema=QaResult,
                metadata={"agent": "qa", "run_id": state.run_id},
            )
            result.findings = list(dict.fromkeys([*deterministic_findings, *result.findings]))
            state.qa_result = result
            state.workflow_status = "qa_completed"
        except Exception as exc:  # noqa: BLE001
            raise FlowForgeError("QA Agent failed.") from exc
        return state

    @staticmethod
    def _qa_emphasis(category: str) -> str:
        if category == "bug":
            return "reproduction coverage, fix validation, regression protection, and operational risk"
        return "requirements coverage, UX/API impact, edge cases, rollout readiness, and test coverage"
