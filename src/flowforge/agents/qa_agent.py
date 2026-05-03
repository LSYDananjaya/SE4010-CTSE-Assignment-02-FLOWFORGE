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
        # QA depends on the prior agents so validation can compare intent, context, and plan.
        if state.intake_result is None or state.context_bundle is None or state.plan_result is None:
            raise FlowForgeError("QA Agent requires intake, context, and planning outputs.")

        try:
            # Run deterministic checks first so rule violations cannot be hidden by the LLM.
            deterministic_findings = self.tool.run(
                intake=state.intake_result,
                context=state.context_bundle,
                plan=state.plan_result,
                workflow_constraints=state.request.constraints,
                observability_enabled=True,
            )
            # Trace metadata keeps the QA stage auditable without storing the full prompt.
            state.trace_context["qa"] = {
                "agent_input_summary": (
                    f"category={state.intake_result.category}, tasks={len(state.plan_result.tasks)}, deterministic_findings={len(deterministic_findings)}"
                ),
                "tool_name": "QaValidatorTool",
                "tool_input_summary": "Validates plan completeness, local-only compliance, observability coverage, and category-specific quality.",
                "tool_output_summary": f"deterministic_findings={len(deterministic_findings)}",
                "fallback_used": False,
            }
            # The prompt combines rubric guidance with the compact plan evidence needed for review.
            prompt = (
                f"{QA_PROMPT.strip()}\n\n"
                f"Request category: {state.intake_result.category}\n"
                f"Expected QA emphasis: {self._qa_emphasis(state.intake_result.category)}\n"
                f"Deterministic findings: {deterministic_findings}\n"
                f"Plan summary: {state.plan_result.summary}\n"
                f"Task count: {len(state.plan_result.tasks)}\n"
                f"Overall risks: {state.plan_result.overall_risks}"
            )
            # Structured output lets downstream workflow state consume QA decisions consistently.
            result = self.llm_client.generate_structured(
                prompt=prompt,
                schema=QaResult,
                metadata={"agent": "qa", "run_id": state.run_id},
            )
            # Preserve deterministic findings while dropping LLM notes that duplicate known plan risks.
            result.findings = self._filter_llm_findings(
                deterministic_findings=deterministic_findings,
                llm_findings=result.findings,
                plan=state.plan_result,
            )
            # A clean findings list means the QA gate can approve the plan.
            if not result.findings:
                result.approved = True
            state.qa_result = result
            state.trace_context["qa"]["llm_output_summary"] = (
                f"approved={result.approved}, findings={len(result.findings)}, rubric_checks={len(result.rubric_checks)}"
            )
            state.workflow_status = "qa_completed"
        except FlowForgeError as exc:
            if "Ollama structured generation failed." not in str(exc):
                state.trace_context.setdefault("qa", {})["failure_cause"] = str(exc)
                raise FlowForgeError("QA Agent failed.") from exc
            state.qa_result = self._build_fallback_result(
                category=state.intake_result.category,
                deterministic_findings=deterministic_findings,
            )
            state.trace_context["qa"]["fallback_used"] = True
            state.trace_context["qa"]["llm_output_summary"] = (
                f"approved={state.qa_result.approved}, findings={len(state.qa_result.findings)}, rubric_checks={len(state.qa_result.rubric_checks)}"
            )
            state.workflow_status = "qa_completed"
        except Exception as exc:  # noqa: BLE001
            state.trace_context.setdefault("qa", {})["failure_cause"] = str(exc)
            raise FlowForgeError("QA Agent failed.") from exc
        return state

    @staticmethod
    def _qa_emphasis(category: str) -> str:
        if category == "bug":
            return "reproduction coverage, fix validation, regression protection, and operational risk"
        return "requirements coverage, UX/API impact, edge cases, rollout readiness, and test coverage"

    @staticmethod
    def _build_fallback_result(*, category: str, deterministic_findings: list[str]) -> QaResult:
        """Return a deterministic QA result when structured generation fails."""
        approved = not deterministic_findings
        rubric_checks = {
            "local_only": approved,
            "observability": approved,
            "tests_present": approved,
        }
        if category == "bug":
            rubric_checks["bug_quality"] = approved
        else:
            rubric_checks["feature_quality"] = approved
        summary = (
            "Deterministic fallback QA approval because structured generation failed."
            if approved
            else "Deterministic fallback QA rejection because rule-based findings remain unresolved."
        )
        return QaResult(
            approved=approved,
            findings=list(dict.fromkeys(deterministic_findings)),
            rubric_checks=rubric_checks,
            summary=summary,
        )

    @staticmethod
    def _filter_llm_findings(
        *,
        deterministic_findings: list[str],
        llm_findings: list[str],
        plan: PlanResult,
    ) -> list[str]:
        """Remove model findings that simply restate documented risks."""
        risk_text = {risk.strip().lower() for risk in plan.overall_risks}
        risk_text.update(risk.strip().lower() for task in plan.tasks for risk in task.risks)
        filtered = [
            finding
            for finding in llm_findings
            if finding.strip().lower() not in risk_text
        ]
        return list(dict.fromkeys([*deterministic_findings, *filtered]))
