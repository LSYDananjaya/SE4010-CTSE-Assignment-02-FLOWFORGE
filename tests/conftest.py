from __future__ import annotations

import json
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
import sys

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Create a small local repository fixture for retrieval tests."""
    repo = tmp_path / "sample_repo"
    (repo / "src").mkdir(parents=True)
    (repo / "tests").mkdir(parents=True)
    (repo / "README.md").write_text(
        "# Demo Repo\n\nBug reports mention auth, export, and timeout behavior.\n",
        encoding="utf-8",
    )
    (repo / "src" / "auth_service.py").write_text(
        "def login(username: str, password: str) -> bool:\n"
        "    # TODO: timeout handling\n"
        "    return bool(username and password)\n",
        encoding="utf-8",
    )
    (repo / "src" / "export_tasks.py").write_text(
        "def export_tasks(format_name: str) -> str:\n"
        "    return f'exported:{format_name}'\n",
        encoding="utf-8",
    )
    (repo / "tests" / "test_auth_service.py").write_text(
        "def test_login_truthy() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )
    return repo


@pytest.fixture
def sample_request_file(tmp_path: Path) -> Path:
    """Create a representative structured request file."""
    payload = {
        "title": "Login request times out after 30 seconds",
        "description": "Users report the login process stalls and then fails.",
        "request_type": "bug",
        "constraints": ["Keep changes local", "Preserve existing login API"],
        "reporter": "qa-team",
    }
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class StubLLM:
    """Simple deterministic LLM stub for agent tests."""

    def __init__(self, responses: list[dict[str, object]]) -> None:
        self._responses = responses
        self.calls: list[dict[str, object]] = []

    def generate_structured(
        self,
        *,
        prompt: str,
        schema: type[object],
        metadata: dict[str, object] | None = None,
    ) -> object:
        self.calls.append(
            {"prompt": prompt, "schema": getattr(schema, "__name__", str(schema)), "metadata": metadata or {}}
        )
        if not self._responses:
            raise AssertionError("No more stub responses configured.")
        response = self._responses.pop(0)
        return schema.model_validate(response)  # type: ignore[attr-defined]
