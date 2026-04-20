from __future__ import annotations

from pathlib import Path

from flowforge.launcher.models import SuggestionCandidate

_SKIP_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".tox", "dist", "build", ".eggs"}


class FileSuggester:
    """Suggest workspace files for @-mention attachment completion."""

    def suggest(self, *, workspace_root: Path, query: str, limit: int = 12) -> list[SuggestionCandidate]:
        """Return fuzzy file suggestions within the selected workspace."""
        lowered = query.lower().strip()
        candidates: list[SuggestionCandidate] = []
        for path in self._walk(workspace_root):
            if not path.is_file():
                continue
            relative = str(path.relative_to(workspace_root)).replace("\\", "/")
            score = self._score(relative.lower(), lowered)
            if score <= 0:
                continue
            candidates.append(SuggestionCandidate(display=relative, value=relative))
        candidates.sort(key=lambda item: (self._score(item.value.lower(), lowered) * -1, item.value))
        return candidates[:limit]

    @staticmethod
    def _walk(root: Path) -> list[Path]:
        """Walk the workspace tree, skipping hidden and environment directories."""
        results: list[Path] = []
        try:
            for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if child.name in _SKIP_DIRS or child.name.startswith("."):
                    continue
                if child.is_file():
                    results.append(child)
                elif child.is_dir():
                    results.extend(FileSuggester._walk(child))
        except OSError:
            pass
        return results

    @staticmethod
    def move_selection(*, current_index: int, direction: str, total: int) -> int:
        """Wrap selection changes for arrow-key navigation."""
        if total <= 0:
            return 0
        delta = 1 if direction == "down" else -1
        return (current_index + delta) % total

    @staticmethod
    def _score(candidate: str, query: str) -> int:
        """Very small fuzzy score based on substring and token presence."""
        if not query:
            return 1
        if query in candidate:
            return len(query) + 10
        score = 0
        for part in query.split():
            if part in candidate:
                score += len(part)
        return score
