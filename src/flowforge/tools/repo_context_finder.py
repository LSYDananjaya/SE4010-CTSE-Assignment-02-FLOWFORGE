from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from flowforge.models.outputs import RetrievalCandidate
from flowforge.utils.errors import ToolExecutionError


ALLOWED_SUFFIXES = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml",
    ".ts", ".tsx", ".js", ".jsx", ".css", ".scss", ".html", ".vue", ".svelte",
    ".go", ".rs", ".java", ".kt", ".rb", ".toml", ".cfg", ".ini",
}

_SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    ".mypy_cache", ".pytest_cache", ".tox", "dist", "build",
    ".eggs", ".next", ".nuxt", "coverage", ".turbo", ".cache",
}


class RetrievalResult(BaseModel):
    """Deterministic retrieval output prior to LLM selection."""

    candidates: list[RetrievalCandidate] = Field(default_factory=list)
    files_considered: int = 0
    missing_attachments: list[str] = Field(default_factory=list)


class RepoContextFinderTool:
    """Retrieve relevant local repository files with lightweight scoring."""

    def __init__(self, *, max_files: int = 5, snippet_chars: int = 600) -> None:
        self.max_files = max_files
        self.snippet_chars = snippet_chars

    def run(
        self,
        *,
        repo_path: str | Path,
        query: str,
        constraints: list[str],
        attachments: list[str] | None = None,
    ) -> RetrievalResult:
        """Find high-signal files using keyword overlap against the query."""
        try:
            root = Path(repo_path).resolve(strict=True)
            if not root.is_dir():
                raise ToolExecutionError(f"Repository path is not a directory: {root}")

            keywords = {part.lower() for part in query.replace("\n", " ").split() if len(part) > 2}
            scored: list[RetrievalCandidate] = []
            seen_paths: set[str] = set()
            missing_attachments: list[str] = []

            for attachment in attachments or []:
                candidate = (root / attachment).resolve()
                try:
                    relative_path = candidate.relative_to(root)
                except ValueError:
                    missing_attachments.append(attachment)
                    continue
                if not candidate.exists() or not candidate.is_file():
                    missing_attachments.append(attachment)
                    continue
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    missing_attachments.append(attachment)
                    continue
                normalized_path = str(relative_path).replace("\\", "/")
                seen_paths.add(normalized_path)
                scored.append(
                    RetrievalCandidate(
                        path=normalized_path,
                        score=max(len(keywords), 1) + 100,
                        language=candidate.suffix.lstrip(".") or "text",
                        content=content[: self.snippet_chars],
                    )
                )

            for file_path in self._walk(root):
                if not file_path.is_file() or file_path.suffix.lower() not in ALLOWED_SUFFIXES:
                    continue
                relative_path = str(file_path.relative_to(root)).replace("\\", "/")
                if relative_path in seen_paths:
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                lowered = content.lower()
                score = sum(1 for keyword in keywords if keyword in lowered or keyword in file_path.name.lower())
                if score <= 0:
                    continue
                snippet = content[: self.snippet_chars]
                scored.append(
                    RetrievalCandidate(
                        path=relative_path,
                        score=score,
                        language=file_path.suffix.lstrip(".") or "text",
                        content=snippet,
                    )
                )

            scored.sort(key=lambda item: (-item.score, item.path))
            return RetrievalResult(
                candidates=scored[: self.max_files],
                files_considered=len(scored),
                missing_attachments=missing_attachments,
            )
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, ToolExecutionError):
                raise
            raise ToolExecutionError("Repository context finder failed.") from exc

    @staticmethod
    def _walk(root: Path) -> list[Path]:
        """Walk the repo tree, skipping irrelevant directories."""
        results: list[Path] = []
        try:
            for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
                if child.name in _SKIP_DIRS or child.name.startswith("."):
                    continue
                if child.is_file():
                    results.append(child)
                elif child.is_dir():
                    results.extend(RepoContextFinderTool._walk(child))
        except OSError:
            pass
        return results
