from __future__ import annotations

import sqlite3
from pathlib import Path

from flowforge.models.outputs import ArtifactPaths


class PersistenceService:
    """Store run metadata in SQLite."""

    def __init__(self, *, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.database_path = self.base_dir / "app.db"
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""
        return sqlite3.connect(self.database_path)

    def _ensure_schema(self) -> None:
        """Create tables if they do not already exist."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    request_title TEXT NOT NULL,
                    workflow_status TEXT NOT NULL,
                    qa_approved INTEGER NOT NULL,
                    markdown_report TEXT NOT NULL,
                    json_report TEXT NOT NULL,
                    trace_file TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS recent_projects (
                    path TEXT PRIMARY KEY,
                    last_used_at TEXT NOT NULL
                )
                """
            )

    def record_run(
        self,
        *,
        run_id: str,
        request_title: str,
        workflow_status: str,
        qa_approved: bool,
        artifacts: ArtifactPaths,
    ) -> None:
        """Insert or replace a workflow run record."""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO runs (
                    run_id, request_title, workflow_status, qa_approved,
                    markdown_report, json_report, trace_file
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    request_title,
                    workflow_status,
                    int(qa_approved),
                    artifacts.markdown_report,
                    artifacts.json_report,
                    artifacts.trace_file,
                ),
            )

    def fetch_runs(self) -> list[dict[str, object]]:
        """Return all run records as dictionaries."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT run_id, request_title, workflow_status, qa_approved,
                       markdown_report, json_report, trace_file
                FROM runs
                ORDER BY rowid ASC
                """
            )
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def record_recent_project(self, path: str) -> None:
        """Insert or update a recently used project path."""
        from flowforge.utils.time import utc_now_iso

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO recent_projects (path, last_used_at)
                VALUES (?, ?)
                ON CONFLICT(path) DO UPDATE SET last_used_at=excluded.last_used_at
                """,
                (path, utc_now_iso()),
            )

    def fetch_recent_projects(self, limit: int = 5) -> list[dict[str, object]]:
        """Return recent project paths in descending usage order."""
        with self._connect() as connection:
            cursor = connection.execute(
                """
                SELECT path, last_used_at
                FROM recent_projects
                ORDER BY last_used_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
