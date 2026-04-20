from __future__ import annotations

from pathlib import Path

from flowforge.models.outputs import ArtifactPaths
from flowforge.services.persistence import PersistenceService


def test_persistence_service_creates_database_and_run_record(tmp_path: Path) -> None:
    service = PersistenceService(base_dir=tmp_path)
    artifacts = ArtifactPaths(
        markdown_report=str(tmp_path / "report.md"),
        json_report=str(tmp_path / "report.json"),
        trace_file=str(tmp_path / "trace.jsonl"),
    )

    service.record_run(
        run_id="run-123",
        request_title="Login timeout bug",
        workflow_status="completed",
        qa_approved=True,
        artifacts=artifacts,
    )

    rows = service.fetch_runs()
    assert len(rows) == 1
    assert rows[0]["run_id"] == "run-123"
    assert rows[0]["qa_approved"] == 1
