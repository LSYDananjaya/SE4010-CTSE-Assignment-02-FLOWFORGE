from __future__ import annotations

from flowforge.agents.context_agent import ContextAgent
from flowforge.models.outputs import ContextBundle, IntakeResult
from flowforge.models.requests import UserRequest
from flowforge.models.state import WorkflowState
from flowforge.tools.repo_context_finder import RepoContextFinderTool
from flowforge.utils.errors import FlowForgeError


def test_context_agent_retrieves_relevant_snippets(sample_repo) -> None:
    request = UserRequest(
        title="Login timeout bug",
        description="The auth request stalls and times out.",
        request_type="bug",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="bug",
        severity="high",
        scope="backend",
        goals=["Fix login timeout"],
        missing_information=[],
        summary="Fix login timeout.",
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "files_considered": 3,
                "selected_snippets": [
                    {
                        "path": "src/auth_service.py",
                        "language": "python",
                        "reason": "Contains login timeout note",
                        "content": "def login(username: str, password: str) -> bool:\n    # TODO: timeout handling",
                    }
                ],
                "constraints": ["Preserve login API"],
                "summary": "Relevant auth code located.",
            }
        ]
    )

    agent = ContextAgent(llm_client=llm, tool=RepoContextFinderTool())
    updated = agent.run(state)

    assert isinstance(updated.context_bundle, ContextBundle)
    assert updated.context_bundle.selected_snippets
    assert updated.context_bundle.selected_snippets[0].path.endswith("auth_service.py")
    assert updated.workflow_status == "context_completed"


def test_context_agent_prioritizes_attached_file(sample_repo) -> None:
    target = sample_repo / "src" / "components"
    target.mkdir(parents=True)
    (target / "CategoryPicker.tsx").write_text(
        "export const ITEM_CATEGORIES = ['Books'];\n"
        "export function CategoryPicker() { return null; }\n",
        encoding="utf-8",
    )
    request = UserRequest(
        title="what are the improvements i can do on",
        description="what are the improvements i can do on @src/components/CategoryPicker.tsx",
        request_type="feature",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
        attachments=["src/components/CategoryPicker.tsx"],
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="medium",
        scope="frontend",
        goals=["Review CategoryPicker improvements"],
        missing_information=[],
        summary="Review CategoryPicker.",
    )
    llm = __import__("tests.conftest", fromlist=["StubLLM"]).StubLLM(
        [
            {
                "files_considered": 1,
                "selected_snippets": [
                    {
                        "path": "src/components/CategoryPicker.tsx",
                        "language": "tsx",
                        "reason": "Explicitly attached by the user",
                        "content": "export function CategoryPicker() { return null; }",
                    }
                ],
                "constraints": [],
                "summary": "Attached component selected.",
            }
        ]
    )

    updated = ContextAgent(llm_client=llm, tool=RepoContextFinderTool()).run(state)

    assert updated.context_bundle is not None
    assert updated.context_bundle.selected_snippets[0].path == "src/components/CategoryPicker.tsx"


def test_context_agent_returns_empty_context_when_no_matches(sample_repo) -> None:
    request = UserRequest(
        title="Obscure migration request",
        description="Analyze a subsystem that does not exist in this repository.",
        request_type="feature",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="low",
        scope="unknown",
        goals=["Analyze missing subsystem"],
        missing_information=[],
        summary="Analyze a missing subsystem.",
    )

    updated = ContextAgent(llm_client=object(), tool=RepoContextFinderTool()).run(state)

    assert updated.context_bundle is not None
    assert updated.context_bundle.files_considered == 0
    assert updated.context_bundle.selected_snippets == []
    assert "No relevant repository context" in updated.context_bundle.summary


def test_context_agent_reports_missing_attachment(sample_repo) -> None:
    request = UserRequest(
        title="Inspect missing file",
        description="Review @src/components/DoesNotExist.tsx",
        request_type="feature",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
        attachments=["src/components/DoesNotExist.tsx"],
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="low",
        scope="frontend",
        goals=["Inspect missing file"],
        missing_information=[],
        summary="Inspect missing file.",
    )

    with __import__("pytest").raises(FlowForgeError, match="Missing attachment"):
        ContextAgent(llm_client=object(), tool=RepoContextFinderTool()).run(state)


def test_context_agent_falls_back_to_deterministic_context_when_llm_output_is_invalid(sample_repo) -> None:
    target = sample_repo / "src" / "components"
    target.mkdir(parents=True)
    (target / "AnimatedHeroIllustration.tsx").write_text(
        "export function AnimatedHeroIllustration() {\n"
        "  return null;\n"
        "}\n",
        encoding="utf-8",
    )
    request = UserRequest(
        title="what improvements can be done on",
        description="what improvements can be done on @src/components/AnimatedHeroIllustration.tsx",
        request_type="feature",
        constraints=[],
        reporter="qa",
        repo_path=str(sample_repo),
        attachments=["src/components/AnimatedHeroIllustration.tsx"],
    )
    state = WorkflowState.initial(request=request)
    state.intake_result = IntakeResult(
        category="feature",
        severity="medium",
        scope="frontend",
        goals=["Understand improvements for AnimatedHeroIllustration"],
        missing_information=[],
        summary="Review AnimatedHeroIllustration improvements.",
    )

    class InvalidContextLlm:
        def generate_structured(self, **kwargs):  # type: ignore[no-untyped-def]
            raise FlowForgeError("Ollama structured generation failed. metadata={'agent': 'context'} raw_preview=invalid")

    updated = ContextAgent(llm_client=InvalidContextLlm(), tool=RepoContextFinderTool()).run(state)

    assert updated.context_bundle is not None
    assert updated.context_bundle.selected_snippets
    assert updated.context_bundle.selected_snippets[0].path == "src/components/AnimatedHeroIllustration.tsx"
    assert "fallback" in updated.context_bundle.summary.lower()


def test_context_tool_rejects_attachment_path_traversal(sample_repo) -> None:
    tool = RepoContextFinderTool()

    result = tool.run(
        repo_path=sample_repo,
        query="inspect secrets file",
        constraints=["Local only"],
        attachments=["..\\..\\secret.txt"],
    )

    assert result.missing_attachments == ["..\\..\\secret.txt"]
