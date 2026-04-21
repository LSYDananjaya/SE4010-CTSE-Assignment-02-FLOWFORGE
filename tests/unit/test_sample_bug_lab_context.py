from __future__ import annotations

from pathlib import Path

from flowforge.agents.context_agent import ContextAgent
from flowforge.models.outputs import IntakeResult
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.repo_context_finder import RepoContextFinderTool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUG_LAB_ROOT = PROJECT_ROOT / "examples" / "sample_bug_lab"


def test_sample_bug_lab_context_prioritizes_attached_frontend_file() -> None:
    request = UserRequest(
        title="modal validation bug",
        description="Review @client/src/components/EditTaskModal.tsx for validation issues",
        request_type="bug",
        constraints=[],
        reporter="qa",
        repo_path=str(BUG_LAB_ROOT),
        attachments=["client/src/components/EditTaskModal.tsx"],
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="medium",
        scope="frontend",
        goals=["Review modal validation bug"],
        missing_information=[],
        summary="Review modal validation bug.",
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "files_considered": 1,
                "selected_snippets": [
                    {
                        "path": "client/src/components/EditTaskModal.tsx",
                        "language": "tsx",
                        "reason": "Explicitly attached by the user",
                        "content": "export function EditTaskModal() { return null; }",
                    }
                ],
                "constraints": [],
                "summary": "Attached frontend component selected.",
            }
        ]
    )

    updated = ContextAgent(llm_client=llm, tool=RepoContextFinderTool()).run(state)

    assert updated.context_bundle is not None
    assert updated.context_bundle.selected_snippets[0].path == "client/src/components/EditTaskModal.tsx"


def test_sample_bug_lab_context_prioritizes_attached_backend_and_shared_files() -> None:
    request = UserRequest(
        title="status mapping mismatch",
        description=(
            "Investigate @server/src/routes/tasks.ts and @shared/types.ts for a status contract bug"
        ),
        request_type="bug",
        constraints=[],
        reporter="qa",
        repo_path=str(BUG_LAB_ROOT),
        attachments=["server/src/routes/tasks.ts", "shared/types.ts"],
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="medium",
        scope="fullstack",
        goals=["Review status contract mismatch"],
        missing_information=[],
        summary="Review status contract mismatch.",
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "files_considered": 2,
                "selected_snippets": [
                    {
                        "path": "server/src/routes/tasks.ts",
                        "language": "ts",
                        "reason": "Explicitly attached backend route",
                        "content": "export function createTaskRouter() { return null; }",
                    },
                    {
                        "path": "shared/types.ts",
                        "language": "ts",
                        "reason": "Explicitly attached shared contract",
                        "content": "export type TaskStatus = 'todo' | 'in_progress' | 'done';",
                    },
                ],
                "constraints": [],
                "summary": "Attached backend and shared files selected.",
            }
        ]
    )

    updated = ContextAgent(llm_client=llm, tool=RepoContextFinderTool()).run(state)

    assert updated.context_bundle is not None
    selected_paths = [snippet.path for snippet in updated.context_bundle.selected_snippets]
    assert selected_paths == ["server/src/routes/tasks.ts", "shared/types.ts"]
