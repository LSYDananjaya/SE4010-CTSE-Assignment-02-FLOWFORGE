from __future__ import annotations

from flowforge.agents.prompts import PLANNING_PROMPT
from flowforge.models.outputs import PlanResult, PlannedTask
from flowforge.models.state import WorkflowState
from flowforge.tools.task_plan_builder import TaskPlanBuilderTool
from flowforge.utils.errors import FlowForgeError


class PlanningAgent:
    """
    Generate an implementation-ready task plan from intake and repository context.

    The agent keeps the LLM-facing planning prompt separate from deterministic
    plan cleanup so the workflow can explain both the model output and the
    validation decisions in the trace report.
    """

    def __init__(self, *, llm_client: object, tool: TaskPlanBuilderTool) -> None:
        self.llm_client = llm_client
        self.tool = tool

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run planning, normalize the task graph, and record trace context."""
        if state.intake_result is None or state.context_bundle is None:
            raise FlowForgeError("Planning Agent requires intake and context outputs.")

        try:
            # Keep snippet formatting explicit so the local model can separate path evidence from content.
            snippets = "\n\n".join(
                f"Path: {snippet.path}\nReason: {snippet.reason}\nContent:\n{snippet.content}"
                for snippet in state.context_bundle.selected_snippets
            )

            # Trace summaries stay compact because report generation only needs the planning evidence shape.
            state.trace_context["planning"] = {
                "agent_input_summary": (
                    f"category={state.intake_result.category}, goals={len(state.intake_result.goals)}, snippets={len(state.context_bundle.selected_snippets)}"
                ),
                "tool_name": "TaskPlanBuilderTool",
                "tool_input_summary": "Normalizes LLM tasks, validates dependencies, and de-duplicates criteria and risks.",
                "fallback_used": False,
            }

            # The prompt repeats the request category and expected emphasis so bug and feature plans stay distinct.
            prompt = (
                f"{PLANNING_PROMPT.strip()}\n\n"
                f"Request category: {state.intake_result.category}\n"
                f"Expected planning emphasis: {self._planning_emphasis(state.intake_result.category)}\n"
                f"Request summary: {state.intake_result.summary}\n"
                f"Goals: {state.intake_result.goals}\n"
                f"Constraints: {state.context_bundle.constraints or state.request.constraints}\n"
                f"Relevant snippets:\n{snippets}"
            )

            # Structured generation should already match PlanResult, but the tool still enforces plan integrity.
            raw_plan = self.llm_client.generate_structured(
                prompt=prompt,
                schema=PlanResult,
                metadata={"agent": "planning", "run_id": state.run_id},
            )
            state.plan_result = self.tool.run(raw_plan)

            # Store short trace strings rather than full plan payloads to keep terminal and report output readable.
            state.trace_context["planning"]["tool_output_summary"] = (
                f"tasks={len(state.plan_result.tasks)}, overall_risks={len(state.plan_result.overall_risks)}"
            )
            state.trace_context["planning"]["llm_output_summary"] = state.plan_result.summary[:120]
            state.workflow_status = "planning_completed"
        except FlowForgeError as exc:
            if "Ollama structured generation failed." not in str(exc):
                state.trace_context.setdefault("planning", {})["failure_cause"] = str(exc)
                raise FlowForgeError(f"Planning Agent failed: {exc}") from exc

            # Use a deterministic backup only for structured-generation failures; tool errors should surface.
            fallback_plan = self._build_fallback_plan(state)
            state.plan_result = self.tool.run(fallback_plan)
            state.trace_context["planning"]["fallback_used"] = True
            state.trace_context["planning"]["tool_output_summary"] = (
                f"tasks={len(state.plan_result.tasks)}, overall_risks={len(state.plan_result.overall_risks)}"
            )
            state.trace_context["planning"]["llm_output_summary"] = state.plan_result.summary[:120]
            state.workflow_status = "planning_completed"
        except Exception as exc:  # noqa: BLE001
            state.trace_context.setdefault("planning", {})["failure_cause"] = str(exc)
            raise FlowForgeError(f"Planning Agent failed: {exc}") from exc
        return state

    @staticmethod
    def _planning_emphasis(category: str) -> str:
        """Return category-specific guidance injected into the planning prompt."""
        if category == "bug":
            return "reproduction, root cause, fix sequencing, regression risk, and validation"
        return "requirements coverage, design and implementation steps, UX/API impact, edge cases, and rollout"

    @staticmethod
    def _build_fallback_plan(state: WorkflowState) -> PlanResult:
        """
        Build a deterministic backup plan when structured generation fails.

        The fallback mirrors the same high-level phases requested from the LLM:
        scope the work, implement safely, then validate with regression checks.
        """
        if state.intake_result is None:
            raise FlowForgeError("Planning fallback requires intake output.")

        constraints = state.context_bundle.constraints or state.request.constraints if state.context_bundle else state.request.constraints

        if state.intake_result.category == "bug":
            # Bug plans emphasize reproduction first so fixes are tied to an observable failure.
            tasks = [
                PlannedTask(
                    task_id="T1",
                    title="Reproduce and scope the defect",
                    description="Confirm the timeout behavior against the retrieved login-related context before changing code.",
                    priority="high",
                    dependencies=[],
                    acceptance_criteria=["A deterministic reproduction path is documented."],
                    risks=["The timeout may depend on environment-specific conditions."],
                    owner="Student 3",
                ),
                PlannedTask(
                    task_id="T2",
                    title="Implement the fix without breaking the public API",
                    description="Apply the backend correction while preserving externally visible login behavior and local-only constraints.",
                    priority="high",
                    dependencies=["T1"],
                    acceptance_criteria=["The timeout defect is resolved and existing API behavior is preserved."],
                    risks=["The fix may introduce authentication regressions if request handling changes."],
                    owner="Student 3",
                ),
                PlannedTask(
                    task_id="T3",
                    title="Validate and add regression coverage",
                    description="Run targeted tests or checks that confirm the fix and guard against future regressions.",
                    priority="medium",
                    dependencies=["T2"],
                    acceptance_criteria=["Regression coverage exists for the timeout scenario."],
                    risks=["Validation may miss edge cases if the failing path is not fully reproduced."],
                    owner="Student 3",
                ),
            ]
            summary = "Deterministic fallback plan for a bug report covering reproduction, fix implementation, and regression validation."
            overall_risks = [
                "The reproduced timeout path may depend on local environment timing.",
                "Backend fixes can regress the login flow if validation is incomplete.",
            ]
        else:
            # Feature plans start with scope confirmation to avoid implementing beyond retrieved evidence.
            tasks = [
                PlannedTask(
                    task_id="T1",
                    title="Confirm requirements and impacted files",
                    description="Review the retrieved context and restate the feature expectations, constraints, and touched surfaces.",
                    priority="high",
                    dependencies=[],
                    acceptance_criteria=["The impacted files and feature scope are explicitly identified."],
                    risks=["Context may miss secondary files affected by the change."],
                    owner="Student 3",
                ),
                PlannedTask(
                    task_id="T2",
                    title="Implement the feature increment",
                    description="Apply the feature changes while respecting local-only execution and any API or UX constraints in the request.",
                    priority="high",
                    dependencies=["T1"],
                    acceptance_criteria=["The requested feature behavior is implemented in the impacted files."],
                    risks=["Implementation may alter UI or API expectations if scope is too broad."],
                    owner="Student 3",
                ),
                PlannedTask(
                    task_id="T3",
                    title="Validate behavior and edge cases",
                    description="Add or run checks that confirm the new feature works and does not break adjacent behavior.",
                    priority="medium",
                    dependencies=["T2"],
                    acceptance_criteria=["Feature validation covers the main flow and key edge cases."],
                    risks=["Edge cases may remain uncovered if validation is too narrow."],
                    owner="Student 3",
                ),
            ]
            summary = "Deterministic fallback plan for a feature request covering scope confirmation, implementation, and validation."
            overall_risks = [
                "Feature scope may be broader than the retrieved context suggests.",
                "Validation may miss UX or integration edge cases.",
            ]

        if constraints:
            overall_risks.append(f"Constraints to preserve during implementation: {', '.join(constraints)}.")

        return PlanResult(summary=summary, tasks=tasks, overall_risks=overall_risks)
