from __future__ import annotations

from pathlib import Path

import pytest

from flowforge.launcher.project_selector import ProjectSelector, ProjectValidation
from flowforge.services.persistence import PersistenceService


def test_project_selector_returns_recent_projects_in_reverse_order(tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path)
    selector = ProjectSelector(persistence=persistence)

    project_one = tmp_path / "project_one"
    project_two = tmp_path / "project_two"
    project_one.mkdir()
    project_two.mkdir()

    persistence.record_recent_project(str(project_one))
    persistence.record_recent_project(str(project_two))

    recents = selector.get_recent_projects(limit=5)
    assert [entry.path for entry in recents] == [str(project_two), str(project_one)]


def test_project_selector_lists_directory_choices_with_parent_option(tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path / "data")
    selector = ProjectSelector(persistence=persistence)

    root = tmp_path / "workspace"
    root.mkdir()
    (root / "app").mkdir()
    (root / "docs").mkdir()
    (root / "README.md").write_text("ignore file", encoding="utf-8")

    choices = selector.list_directory_choices(root)
    labels = [choice.label for choice in choices]

    assert labels[0] == ".."
    assert "app" in labels
    assert "docs" in labels
    assert "README.md" not in labels


def test_project_selector_detects_project_markers(sample_repo: Path, tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path)
    selector = ProjectSelector(persistence=persistence)

    validation = selector.validate_project_path(sample_repo)

    assert isinstance(validation, ProjectValidation)
    assert validation.exists is True
    assert validation.is_directory is True
    assert validation.project_like is True
    assert "src" in validation.markers or "README.md" in validation.markers


def test_project_selector_rejects_missing_path(tmp_path: Path) -> None:
    persistence = PersistenceService(base_dir=tmp_path)
    selector = ProjectSelector(persistence=persistence)

    with pytest.raises(ValueError):
        selector.validate_project_path(tmp_path / "does-not-exist")
