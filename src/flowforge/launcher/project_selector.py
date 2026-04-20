from __future__ import annotations

from pathlib import Path

from flowforge.launcher.models import DirectoryChoice, ProjectValidation, RecentProject
from flowforge.services.persistence import PersistenceService


PROJECT_MARKERS = (".git", "src", "package.json", "pyproject.toml", "requirements.txt", "README.md")


class ProjectSelector:
    """Headless project-selection logic for the launcher."""

    def __init__(self, *, persistence: PersistenceService) -> None:
        self.persistence = persistence

    def get_recent_projects(self, limit: int = 5) -> list[RecentProject]:
        """Return recent projects in descending usage order."""
        rows = self.persistence.fetch_recent_projects(limit=limit)
        return [RecentProject(path=str(row["path"]), label=Path(str(row["path"])).name or str(row["path"])) for row in rows]

    def list_directory_choices(self, root: Path, limit: int = 12) -> list[DirectoryChoice]:
        """List directories under a root for numbered terminal browsing."""
        resolved = root.resolve(strict=True)
        directories = sorted(
            [path for path in resolved.iterdir() if path.is_dir()],
            key=lambda item: item.name.lower(),
        )
        choices = [
            DirectoryChoice(key="0", label="..", path=str(resolved.parent), kind="parent"),
            DirectoryChoice(key="1", label=".", path=str(resolved), kind="current"),
        ]
        for index, path in enumerate(directories[:limit], start=2):
            choices.append(DirectoryChoice(key=str(index), label=path.name, path=str(path), kind="directory"))
        return choices

    def validate_project_path(self, path: str | Path) -> ProjectValidation:
        """Validate a selected project folder and detect project markers."""
        candidate = Path(path)
        if not candidate.exists():
            raise ValueError(f"Project path does not exist: {candidate}")
        if not candidate.is_dir():
            raise ValueError(f"Project path is not a directory: {candidate}")

        markers = [marker for marker in PROJECT_MARKERS if (candidate / marker).exists()]
        return ProjectValidation(
            path=str(candidate.resolve()),
            exists=True,
            is_directory=True,
            project_like=bool(markers),
            markers=markers,
        )

