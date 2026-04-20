from __future__ import annotations

from pathlib import Path

from flowforge.launcher.models import RequestDraft
from flowforge.models.requests import UserRequest


class RequestSelector:
    """Headless request selection and normalization logic."""

    def __init__(self, *, sample_dir: Path) -> None:
        self.sample_dir = sample_dir

    def load_sample(self, sample_type: str, *, repo_path: str) -> UserRequest:
        """Load a bundled sample request by short name."""
        mapping = {
            "bug": self.sample_dir / "bug_report_login_timeout.json",
            "feature": self.sample_dir / "feature_request_export_tasks.json",
        }
        if sample_type not in mapping:
            raise ValueError(f"Unknown sample type: {sample_type}")
        return self.load_json_request(mapping[sample_type], repo_path=repo_path)

    def load_json_request(self, path: Path, *, repo_path: str) -> UserRequest:
        """Load a request from an arbitrary JSON file."""
        return UserRequest.from_json_file(path, repo_path=repo_path)

    def from_draft(self, draft: RequestDraft, *, repo_path: str) -> UserRequest:
        """Convert terminal-authored input into a workflow request."""
        return UserRequest(
            title=draft.title,
            description=draft.description,
            request_type=draft.request_type,
            constraints=[value.strip() for value in draft.constraints if value.strip()],
            reporter=draft.reporter,
            repo_path=repo_path,
            attachments=draft.attachments,
        )
