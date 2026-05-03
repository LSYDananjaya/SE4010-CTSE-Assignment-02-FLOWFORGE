from __future__ import annotations

import re

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
            state.trace_context["intake"] = {
                "agent_input_summary": f"title={state.request.title!r}, request_type={state.request.request_type}, constraints={len(state.request.constraints)}",
                "tool_name": "IntakeParserTool",
                "tool_input_summary": "Normalized raw request title, description, and constraints.",
                "tool_output_summary": f"title={parsed.title!r}, request_type={parsed.request_type}, constraints={len(parsed.constraints)}",
                "fallback_used": False,
            }
            prompt = (
                f"{INTAKE_PROMPT.strip()}\n\n"
                f"Title: {parsed.title}\n"
                f"Type: {parsed.request_type}\n"
                f"Description: {parsed.description}\n"
                f"Constraints: {parsed.constraints}"
            )
            try:
                result = self.llm_client.generate_structured(
                    prompt=prompt,
                    schema=IntakeResult,
                    metadata={"agent": "intake", "run_id": state.run_id},
                )
            except Exception as exc:  # noqa: BLE001
                fallback = self._build_fallback_result(
                    title=parsed.title,
                    description=parsed.description,
                    request_type=parsed.request_type,
                    constraints=parsed.constraints,
                    attachments=state.request.attachments,
                )
                state.trace_context["intake"]["fallback_used"] = True
                state.trace_context["intake"]["failure_cause"] = str(exc)
                state.trace_context["intake"]["tool_output_summary"] = (
                    f"{state.trace_context['intake']['tool_output_summary']}; fallback=deterministic"
                )
                state.trace_context["intake"]["llm_output_summary"] = (
                    f"fallback category={fallback.category}, severity={fallback.severity}, scope={fallback.scope}"
                )
                state.intake_result = fallback
                state.workflow_status = "intake_completed"
                return state
            state.intake_result = result
            state.trace_context["intake"]["llm_output_summary"] = (
                f"category={result.category}, severity={result.severity}, goals={len(result.goals)}, missing_info={len(result.missing_information)}"
            )
            state.workflow_status = "intake_completed"
        except Exception as exc:  # noqa: BLE001
            state.trace_context.setdefault("intake", {})["failure_cause"] = str(exc)
            raise FlowForgeError("Intake Agent failed.") from exc
        return state

    @staticmethod
    def _build_fallback_result(
        *,
        title: str,
        description: str,
        request_type: str,
        constraints: list[str],
        attachments: list[str],
    ) -> IntakeResult:
        """Return a deterministic intake result when structured generation is invalid."""
        text = f"{title}\n{description}".lower()
        lowered_attachments = [path.lower() for path in attachments]
        goals: list[str] = []
        if attachments:
            goals.append(f"Review attached files: {', '.join(attachments[:2])}")
        if request_type == "bug":
            goals.append("Identify the root cause and validate the fix safely")
        else:
            goals.append("Identify concrete improvements grounded in the attached/requested code")
        if constraints:
            goals.append(f"Respect constraints: {', '.join(constraints[:2])}")
        return IntakeResult(
            category=request_type,
            severity=IntakeAgent._infer_severity(text),
            scope=IntakeAgent._infer_scope(text, lowered_attachments),
            goals=goals[:3],
            missing_information=[],
            summary=IntakeAgent._build_summary(title, description),
        )

    @staticmethod
    def _infer_severity(text: str) -> str:
        if any(token in text for token in ("crash", "security", "data loss", "broken", "timeout", "failing", "fails")):
            return "high"
        if any(token in text for token in ("improve", "feature", "review", "enhance", "ui", "component")):
            return "medium"
        return "low"

    @staticmethod
    def _infer_scope(text: str, attachments: list[str]) -> str:
        joined = " ".join(attachments)
        if any(token in text or token in joined for token in ("component", ".tsx", ".jsx", "ui", "frontend", "page", "screen", "css")):
            return "frontend"
        if any(token in text or token in joined for token in ("api", "backend", "server", "auth", ".py", ".ts", "database")):
            return "backend"
        if any(token in text for token in ("fullstack", "end-to-end")):
            return "fullstack"
        return "unknown"

    @staticmethod
    def _build_summary(title: str, description: str) -> str:
        compact = re.sub(r"\s+", " ", f"{title}. {description}").strip()
        return compact[:160]
