from __future__ import annotations

import json
from pathlib import Path

from flowforge.models.requests import UserRequest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUG_LAB_ROOT = PROJECT_ROOT / "examples" / "sample_bug_lab"
README_PATH = BUG_LAB_ROOT / "README.md"
SAMPLE_INPUTS = PROJECT_ROOT / "sample_inputs"

REQUEST_FIXTURES = [
    "sample_bug_lab_bug_high_backend_auth.json",
    "sample_bug_lab_bug_medium_frontend_modal.json",
    "sample_bug_lab_bug_medium_fullstack_status.json",
    "sample_bug_lab_bug_low_frontend_sorting.json",
    "sample_bug_lab_feature_dashboard.json",
]


def test_sample_bug_lab_readme_documents_bug_matrix_and_prompts() -> None:
    content = README_PATH.read_text(encoding="utf-8")

    assert "High / Backend" in content
    assert "Medium / Frontend" in content
    assert "Medium / Fullstack" in content
    assert "Low / Frontend" in content
    assert "Low / Backend" in content
    assert "Recommended FlowForge prompts" in content


def test_sample_bug_lab_request_fixtures_are_valid_and_attachment_ready() -> None:
    for fixture_name in REQUEST_FIXTURES:
        fixture_path = SAMPLE_INPUTS / fixture_name
        request = UserRequest.from_json_file(fixture_path, repo_path=str(BUG_LAB_ROOT))

        assert request.repo_path == str(BUG_LAB_ROOT)
        assert request.attachments

        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        assert payload["request_type"] in {"bug", "feature"}

        for attachment in request.attachments:
            target = BUG_LAB_ROOT / attachment
            assert target.exists(), f"{fixture_name} points to missing attachment {attachment}"


def test_sample_bug_lab_contains_expected_multisurface_files() -> None:
    expected_files = [
        BUG_LAB_ROOT / "client" / "src" / "components" / "FeatureCard.tsx",
        BUG_LAB_ROOT / "client" / "src" / "components" / "EditTaskModal.tsx",
        BUG_LAB_ROOT / "client" / "src" / "api" / "tasks.ts",
        BUG_LAB_ROOT / "server" / "src" / "routes" / "auth.ts",
        BUG_LAB_ROOT / "server" / "src" / "routes" / "tasks.ts",
        BUG_LAB_ROOT / "server" / "src" / "services" / "taskStore.ts",
        BUG_LAB_ROOT / "shared" / "types.ts",
    ]

    for expected_file in expected_files:
        assert expected_file.exists(), f"Missing sample bug lab file: {expected_file}"
