from __future__ import annotations

from flowforge.agents.intake_agent import IntakeAgent
from flowforge.models.outputs import IntakeResult
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.intake_parser import IntakeParserTool
from flowforge.utils.errors import FlowForgeError
from flowforge.utils.errors import ToolExecutionError


def test_intake_agent_normalizes_request_and_updates_state() -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Login waits for 30 seconds and fails for valid users.",
        request_type="bug",
        constraints=["Keep auth API stable"],
        reporter="qa",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "category": "bug",
                "severity": "high",
                "scope": "backend",
                "goals": ["Fix timeout handling", "Preserve login API"],
                "missing_information": [],
                "summary": "Investigate and fix login timeout behavior.",
            }
        ]
    )

    agent = IntakeAgent(llm_client=llm, tool=IntakeParserTool())
    updated = agent.run(state)

    assert isinstance(updated.intake_result, IntakeResult)
    assert updated.intake_result.category == "bug"
    assert updated.intake_result.severity == "high"
    assert updated.workflow_status == "intake_completed"
    assert updated.errors == []


def test_intake_parser_rejects_empty_request_content() -> None:
    request = UserRequest(
        title="Valid title",
        description="          ",
        request_type="bug",
        constraints=["  "],
        reporter="qa",
        repo_path="C:/repo",
    )

    with __import__("pytest").raises(ToolExecutionError, match="missing meaningful title or description"):
        IntakeParserTool().run(request)


def test_intake_agent_falls_back_when_structured_output_is_invalid() -> None:
    request = UserRequest(
        title="what are the improvements can be done on",
        description="what are the improvements can be done on @src/components/FeatureCard.tsx",
        request_type="feature",
        constraints=[],
        reporter="qa",
        repo_path="C:/repo",
        attachments=["src/components/FeatureCard.tsx"],
    )
    state = WorkflowState.initial(request=request)
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "category": "feature",
                "severity": "unknown",
                "scope": "fullstack",
                "goals": ["identify improvements"],
                "missing_information": [],
                "summary": "Review improvements.",
            }
        ]
    )

    updated = IntakeAgent(llm_client=llm, tool=IntakeParserTool()).run(state)

    assert updated.intake_result is not None
    assert updated.intake_result.severity in {"low", "medium", "high"}
    assert updated.intake_result.scope in {"backend", "frontend", "fullstack", "unknown"}
    assert updated.workflow_status == "intake_completed"
    assert updated.trace_context["intake"]["fallback_used"] is True
    assert "validation" in updated.trace_context["intake"]["failure_cause"].lower()


def test_intake_agent_preserves_real_failure_when_parser_fails() -> None:
    request = UserRequest(
        title="ok title",
        description="          ",
        request_type="bug",
        constraints=[],
        reporter="qa",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)

    with __import__("pytest").raises(FlowForgeError, match="Intake Agent failed"):
        IntakeAgent(llm_client=object(), tool=IntakeParserTool()).run(state)
