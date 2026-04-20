from __future__ import annotations

from flowforge.agents.qa_agent import QAAgent
from flowforge.models.outputs import ContextBundle, FileSnippet, IntakeResult, PlanResult, PlannedTask, QaResult
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.qa_validator import QaValidatorTool


def test_qa_agent_flags_and_approves_complete_plan() -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix timeout and keep it local.",
        request_type="bug",
        constraints=["Local only"],
        reporter="qa",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="high",
        scope="backend",
        goals=["Fix timeout"],
        missing_information=[],
        summary="Fix timeout.",
    )
    state.context_bundle = ContextBundle(
        files_considered=1,
        selected_snippets=[
            FileSnippet(
                path="src/auth_service.py",
                language="python",
                reason="Relevant login path",
                content="def login(username: str, password: str) -> bool:\n    return True",
            )
        ],
        constraints=[],
        summary="Context found.",
    )
    state.plan_result = PlanResult(
        summary="Fix login timeout and test it.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Fix timeout",
                description="Update timeout handling.",
                priority="high",
                dependencies=[],
                acceptance_criteria=["Login timeout handled gracefully"],
                risks=["Regression in auth flow"],
                owner="Student 4",
            )
        ],
        overall_risks=["Regression in auth flow"],
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "approved": True,
                "findings": [],
                "rubric_checks": {
                    "four_agents": True,
                    "local_only": True,
                    "observability": True,
                    "tests_present": True,
                },
                "summary": "Plan is complete and compliant.",
            }
        ]
    )

    agent = QAAgent(llm_client=llm, tool=QaValidatorTool())
    updated = agent.run(state)

    assert isinstance(updated.qa_result, QaResult)
    assert updated.qa_result.approved is True
    assert updated.workflow_status == "qa_completed"
    assert "Request category: bug" in llm.calls[0]["prompt"]


def test_qa_agent_uses_feature_specific_rubric_language() -> None:
    request = UserRequest(
        title="Category picker improvements",
        description="Suggest improvements for CategoryPicker.",
        request_type="feature",
        constraints=["Local only"],
        reporter="pm",
        repo_path="C:/repo",
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="medium",
        scope="frontend",
        goals=["Improve CategoryPicker UX"],
        missing_information=[],
        summary="Improve CategoryPicker UX.",
    )
    state.context_bundle = ContextBundle(
        files_considered=1,
        selected_snippets=[
            FileSnippet(
                path="src/components/CategoryPicker.tsx",
                language="tsx",
                reason="Attached UI component",
                content="export function CategoryPicker() { return null; }",
            )
        ],
        constraints=[],
        summary="Component found.",
    )
    state.plan_result = PlanResult(
        summary="Add search and accessibility improvements.",
        tasks=[
            PlannedTask(
                task_id="T1",
                title="Refine component UX",
                description="Improve accessibility and discoverability.",
                priority="medium",
                dependencies=[],
                acceptance_criteria=["Users can filter categories quickly"],
                risks=["UI regression"],
                owner="Student 4",
            )
        ],
        overall_risks=["UI regression"],
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "approved": True,
                "findings": [],
                "rubric_checks": {
                    "feature_scope": True,
                    "ux_impact": True,
                    "observability": True,
                    "tests_present": True,
                },
                "summary": "Feature plan is complete.",
            }
        ]
    )

    updated = QAAgent(llm_client=llm, tool=QaValidatorTool()).run(state)

    assert updated.qa_result is not None
    assert updated.qa_result.approved is True
    assert "Request category: feature" in llm.calls[0]["prompt"]
    assert "Expected QA emphasis: requirements coverage, UX/API impact" in llm.calls[0]["prompt"]
