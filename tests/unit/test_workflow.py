from __future__ import annotations

from pathlib import Path

from flowforge.graph.nodes import build_agent_node
from flowforge.graph.workflow import FlowForgeWorkflow
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.services.tracing import JsonTraceWriter


def test_workflow_runs_all_agents_with_stubbed_llm(sample_repo) -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix the login timeout issue.",
        request_type="bug",
        constraints=["Local only"],
        reporter="qa",
        repo_path=str(sample_repo),
    )
    responses = [
        {
            "category": "bug",
            "severity": "high",
            "scope": "backend",
            "goals": ["Fix timeout"],
            "missing_information": [],
            "summary": "Fix timeout.",
        },
        {
            "files_considered": 3,
            "selected_snippets": [
                {
                    "path": "src/auth_service.py",
                    "language": "python",
                    "reason": "Contains login logic",
                    "content": "def login(username: str, password: str) -> bool:\n    return bool(username and password)",
                }
            ],
            "constraints": ["Local only"],
            "summary": "Auth snippet found.",
        },
        {
            "summary": "Plan fix and tests.",
            "tasks": [
                {
                    "task_id": "T1",
                    "title": "Patch timeout handling",
                    "description": "Update auth timeout behavior.",
                    "priority": "high",
                    "dependencies": [],
                    "acceptance_criteria": ["Timeout handled gracefully"],
                    "risks": ["Regression in auth flow"],
                    "owner": "Student 3",
                }
            ],
            "overall_risks": ["Regression in auth flow"],
        },
        {
            "approved": True,
            "findings": [],
            "rubric_checks": {
                "four_agents": True,
                "local_only": True,
                "observability": True,
                "tests_present": True,
            },
            "summary": "Plan approved.",
        },
    ]

    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(responses)
    workflow = FlowForgeWorkflow.from_stub_llm(llm)
    result = workflow.run(request)

    assert result.intake_result is not None
    assert result.context_bundle is not None
    assert result.plan_result is not None
    assert result.qa_result is not None
    assert result.workflow_status == "completed"


def test_agent_node_emits_started_and_success_trace_events(sample_repo, tmp_path: Path) -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix the login timeout issue.",
        request_type="bug",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
    )
    writer = JsonTraceWriter(base_dir=tmp_path / "data")
    events: list[dict[str, object]] = []
    writer.on_event = lambda event: events.append(event)

    def runner(workflow: WorkflowState) -> WorkflowState:
        workflow.workflow_status = "intake_completed"
        return workflow

    node = build_agent_node(name="intake", runner=runner, trace_writer=writer)
    workflow = WorkflowState.initial(request=request)

    node({"workflow": workflow})

    assert [event["status"] for event in events] == ["started", "success"]
    assert events[0]["detail"] == ""
    assert events[1]["detail"] == ""


def test_agent_node_emits_detailed_error_trace_event(sample_repo, tmp_path: Path) -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="Fix the login timeout issue.",
        request_type="bug",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
    )
    writer = JsonTraceWriter(base_dir=tmp_path / "data")
    events: list[dict[str, object]] = []
    writer.on_event = lambda event: events.append(event)

    def runner(workflow: WorkflowState) -> WorkflowState:
        raise ValueError("Task T2 references unknown dependencies: ['T9']")

    node = build_agent_node(name="planning", runner=runner, trace_writer=writer)
    workflow = WorkflowState.initial(request=request)

    updated = node({"workflow": workflow})["workflow"]
    trace_rows = writer.read_trace_summary(Path(updated.trace_file))

    assert [event["status"] for event in events] == ["started", "error"]
    assert "unknown dependencies" in str(events[1]["detail"])
    assert updated.errors[0] == "Task T2 references unknown dependencies: ['T9']"
    assert updated.errors[1] == "Planning Agent failed."
    assert [row.status for row in trace_rows] == ["error"]
