from __future__ import annotations

from pathlib import Path

from flowforge.launcher.app import LauncherApp
from flowforge.launcher.request_selector import RequestDraft, RequestSelector
from flowforge.models.requests import UserRequest


def test_request_selector_loads_sample_bug_request() -> None:
    selector = RequestSelector(sample_dir=Path("sample_inputs"))

    request = selector.load_sample("bug", repo_path="C:/repo")

    assert isinstance(request, UserRequest)
    assert request.request_type == "bug"
    assert request.repo_path == "C:/repo"


def test_request_selector_loads_json_request(sample_request_file: Path) -> None:
    selector = RequestSelector(sample_dir=Path("sample_inputs"))

    request = selector.load_json_request(sample_request_file, repo_path="C:/repo")

    assert request.title.startswith("Login request")
    assert request.repo_path == "C:/repo"


def test_request_selector_builds_terminal_authored_request() -> None:
    selector = RequestSelector(sample_dir=Path("sample_inputs"))
    draft = RequestDraft(
        title="Add CSV export",
        request_type="feature",
        description="Allow users to export tasks as CSV.",
        constraints=["Local only", "Keep API stable"],
        reporter="pm",
    )

    request = selector.from_draft(draft, repo_path="C:/repo")

    assert request.request_type == "feature"
    assert request.constraints == ["Local only", "Keep API stable"]
    assert request.reporter == "pm"


def test_launcher_infers_improvement_requests_as_feature() -> None:
    assert (
        LauncherApp._infer_request_type("what are the improvements i can do on @src/components/CategoryPicker.tsx")
        == "feature"
    )


def test_launcher_infers_fix_requests_as_bug() -> None:
    assert LauncherApp._infer_request_type("fix login timeout in auth service") == "bug"
