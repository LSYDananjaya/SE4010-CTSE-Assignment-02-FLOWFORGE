from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from flowforge.launcher.models import TraceSummaryRow
from flowforge.utils.time import utc_now_iso


class JsonTraceWriter:
    """Write one JSON event per line for each workflow run."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = (base_dir or Path("data")).resolve()
        self.trace_dir = self.base_dir / "traces"
        self.trace_dir.mkdir(parents=True, exist_ok=True)
        self.on_event: Callable[[dict[str, Any]], None] | None = None

    def trace_path_for(self, run_id: str) -> str:
        """Return the trace file path for a run."""
        return str(self.trace_dir / f"{run_id}.jsonl")

    def write_event(
        self,
        *,
        run_id: str,
        node_name: str,
        status: str,
        latency_ms: float,
        detail: str = "",
    ) -> None:
        """Append a trace event to the run-specific JSONL file."""
        payload: dict[str, Any] = {
            "timestamp": utc_now_iso(),
            "run_id": run_id,
            "node_name": node_name,
            "status": status,
            "latency_ms": round(latency_ms, 2),
            "detail": detail,
        }
        path = Path(self.trace_path_for(run_id))
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload) + "\n")
        if self.on_event is not None:
            self.on_event(payload)

    def read_trace_summary(self, path: Path) -> list[TraceSummaryRow]:
        """Read a compact trace summary from a JSONL trace file."""
        if not path.exists():
            return []
        rows: list[TraceSummaryRow] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                status = str(payload.get("status", ""))
                if status == "started":
                    continue
                rows.append(
                    TraceSummaryRow(
                        node_name=str(payload.get("node_name", "")),
                        status=status,
                        latency_ms=float(payload.get("latency_ms", 0.0)),
                    )
                )
        return rows
