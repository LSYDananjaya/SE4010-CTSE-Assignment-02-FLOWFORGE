from __future__ import annotations

import json
from pathlib import Path

from flowforge.models.outputs import ArtifactPaths
from flowforge.models.state import WorkflowState


class ReportingService:
    """Write final Markdown and JSON reports to disk."""

    def __init__(self, *, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.report_dir = self.base_dir / "reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def write_reports(self, state: WorkflowState) -> ArtifactPaths:
        """Persist report artifacts for a workflow run."""
        markdown_path = self.report_dir / f"{state.run_id}.md"
        json_path = self.report_dir / f"{state.run_id}.json"
        markdown_path.write_text(self._to_markdown(state), encoding="utf-8")
        json_path.write_text(json.dumps(state.model_dump(mode="json"), indent=2), encoding="utf-8")
        artifacts = ArtifactPaths(
            markdown_report=str(markdown_path),
            json_report=str(json_path),
            trace_file=state.trace_file,
        )
        state.artifacts = artifacts
        return artifacts

    def _to_markdown(self, state: WorkflowState) -> str:
        """Render a concise final engineering report."""
        intake = state.intake_result
        context = state.context_bundle
        plan = state.plan_result
        qa = state.qa_result
        task_lines = []
        if plan:
            for task in plan.tasks:
                task_lines.append(
                    f"- **{task.task_id} {task.title}** ({task.priority})\n"
                    f"  - Owner: {task.owner}\n"
                    f"  - Dependencies: {', '.join(task.dependencies) or 'None'}\n"
                    f"  - Acceptance: {', '.join(task.acceptance_criteria)}\n"
                    f"  - Risks: {', '.join(task.risks)}"
                )
        snippet_lines = []
        if context:
            for snippet in context.selected_snippets:
                snippet_lines.append(f"- `{snippet.path}`: {snippet.reason}")
        return (
            f"# FlowForge Engineering Report\n\n"
            f"## Run\n"
            f"- Run ID: `{state.run_id}`\n"
            f"- Status: `{state.workflow_status}`\n"
            f"- Request: {state.request.title}\n\n"
            f"## Request\n"
            f"- Repo Path: `{state.request.repo_path}`\n"
            f"- Attachments: {', '.join(state.request.attachments) or 'None'}\n\n"
            f"## Intake\n"
            f"- Summary: {intake.summary if intake else 'N/A'}\n"
            f"- Goals: {', '.join(intake.goals) if intake else 'N/A'}\n\n"
            f"## Context\n"
            f"{chr(10).join(snippet_lines) if snippet_lines else '- No snippets selected'}\n\n"
            f"## Plan\n"
            f"{chr(10).join(task_lines) if task_lines else '- No tasks produced'}\n\n"
            f"## QA\n"
            f"- Approved: {qa.approved if qa else False}\n"
            f"- Findings: {', '.join(qa.findings) if qa and qa.findings else 'None'}\n"
        )
