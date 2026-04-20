from __future__ import annotations

from flowforge.agents.intake_agent import IntakeAgent
from flowforge.models.outputs import IntakeResult
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.intake_parser import IntakeParserTool


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
