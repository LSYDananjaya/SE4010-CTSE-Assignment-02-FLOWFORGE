from __future__ import annotations

from flowforge.agents.prompts import CONTEXT_PROMPT
from flowforge.models.outputs import ContextBundle, FileSnippet
from flowforge.models.state import WorkflowState
from flowforge.tools.repo_context_finder import RepoContextFinderTool
from flowforge.utils.errors import FlowForgeError


class ContextAgent:
    """Retrieve and summarize relevant local repository context."""

    def __init__(self, *, llm_client: object, tool: RepoContextFinderTool) -> None:
        self.llm_client = llm_client
        self.tool = tool

    def run(self, state: WorkflowState) -> WorkflowState:
        """Run repository context retrieval and update workflow state."""
        if state.intake_result is None:
            raise FlowForgeError("Context Agent requires intake output.")

        try:
            retrieval = self.tool.run(
                repo_path=state.request.repo_path,
                query=f"{state.request.title}\n{state.request.description}\n{' '.join(state.intake_result.goals)}",
                constraints=state.request.constraints,
                attachments=state.request.attachments,
            )
            if retrieval.missing_attachments:
                joined = ", ".join(retrieval.missing_attachments)
                raise FlowForgeError(f"Missing attachment(s): {joined}")
            if not retrieval.candidates:
                state.context_bundle = ContextBundle(
                    files_considered=0,
                    selected_snippets=[],
                    constraints=state.request.constraints,
                    summary="No relevant repository context found for the current request.",
                )
                state.workflow_status = "context_completed"
                return state
            serialized_candidates = "\n\n".join(
                f"Path: {candidate.path}\nScore: {candidate.score}\nContent:\n{candidate.content}"
                for candidate in retrieval.candidates
            )
            prompt = (
                f"{CONTEXT_PROMPT.strip()}\n\n"
                f"Request category: {state.intake_result.category}\n"
                f"Goals: {state.intake_result.goals}\n"
                f"Constraints: {state.request.constraints}\n"
                f"Attachments: {state.request.attachments}\n"
                f"Retrieved candidates:\n{serialized_candidates}"
            )
            result = self.llm_client.generate_structured(
                prompt=prompt,
                schema=ContextBundle,
                metadata={"agent": "context", "run_id": state.run_id},
            )
            state.context_bundle = result
            state.workflow_status = "context_completed"
        except FlowForgeError as exc:
            if "Ollama structured generation failed." not in str(exc):
                raise
            state.context_bundle = ContextBundle(
                files_considered=retrieval.files_considered,
                selected_snippets=[
                    FileSnippet(
                        path=candidate.path,
                        language=candidate.language,
                        reason="Deterministic fallback selected after structured context generation failed.",
                        content=candidate.content,
                    )
                    for candidate in retrieval.candidates[:2]
                ],
                constraints=state.request.constraints,
                summary=(
                    "Deterministic fallback context generated after structured context generation failed. "
                    f"Root cause: {exc}"
                ),
            )
            state.workflow_status = "context_completed"
        except FlowForgeError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise FlowForgeError(f"Context Agent failed: {exc}") from exc
        return state
