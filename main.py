from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from flowforge.config import AppConfig
from flowforge.graph.workflow import FlowForgeWorkflow
from flowforge.launcher.app import LauncherApp
from flowforge.launcher.prompt_toolkit_io import PromptToolkitPromptIO, prompt_toolkit_available
from flowforge.llm.ollama_client import OllamaStructuredClient
from flowforge.models.requests import UserRequest
from flowforge.services.persistence import PersistenceService
from flowforge.services.reporting import ReportingService
from flowforge.services.tracing import JsonTraceWriter
from flowforge.tui.app import FlowForgeTui


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for FlowForge."""
    parser = argparse.ArgumentParser(description="Run the FlowForge local multi-agent workflow.")
    parser.add_argument("--repo-path", help="Path to the local repository to analyze.")
    parser.add_argument("--input-file", help="Path to the JSON request file.")
    parser.add_argument("--output-dir", default="data", help="Directory for reports, traces, and SQLite data.")
    parser.add_argument("--live-ollama", action="store_true", help="Use live Ollama instead of a test stub.")
    parser.add_argument("--tui", action="store_true", help="Show a Rich-based terminal view.")
    return parser.parse_args()


def build_workflow(
    config: AppConfig,
    use_live_ollama: bool,
) -> tuple[FlowForgeWorkflow, PersistenceService, ReportingService, JsonTraceWriter]:
    """Construct the workflow and supporting services."""
    trace_writer = JsonTraceWriter(base_dir=config.base_dir)
    reporting = ReportingService(base_dir=config.base_dir)
    persistence = PersistenceService(base_dir=config.base_dir)

    if not use_live_ollama:
        raise ValueError("FlowForge requires --live-ollama when running outside tests.")

    llm_client = OllamaStructuredClient(
        base_url=config.ollama_base_url,
        model=config.ollama_model,
        timeout_seconds=config.ollama_timeout_seconds,
    )
    workflow = FlowForgeWorkflow.from_live_llm(llm_client=llm_client, trace_writer=trace_writer)
    return workflow, persistence, reporting, trace_writer


def main() -> None:
    """Run the FlowForge application."""
    args = parse_args()
    config = AppConfig.from_base_dir(Path(args.output_dir))
    workflow, persistence, reporting, trace_writer = build_workflow(config, use_live_ollama=args.live_ollama)
    if args.repo_path and args.input_file:
        request = UserRequest.from_json_file(Path(args.input_file), repo_path=args.repo_path)
        result = workflow.run(request)
        artifacts = reporting.write_reports(result)
        persistence.record_run(
            run_id=result.run_id,
            request_title=result.request.title,
            workflow_status=result.workflow_status,
            qa_approved=bool(result.qa_result and result.qa_result.approved),
            artifacts=artifacts,
        )
        persistence.record_recent_project(args.repo_path)
        if args.tui:
            FlowForgeTui().render(result=result, artifacts=artifacts)
        else:
            print(f"Run ID: {result.run_id}")
            print(f"Workflow status: {result.workflow_status}")
            print(f"Markdown report: {artifacts.markdown_report}")
            print(f"JSON report: {artifacts.json_report}")
            print(f"Trace file: {artifacts.trace_file}")
        return

    if not prompt_toolkit_available():
        raise ModuleNotFoundError(
            "Interactive mode requires prompt_toolkit. Install dependencies with: python -m pip install -r requirements.txt"
        )
    tui = FlowForgeTui()
    prompt_io = PromptToolkitPromptIO()
    launcher = LauncherApp(
        persistence=persistence,
        reporting=reporting,
        trace_writer=trace_writer,
        workflow=workflow,
        prompt_io=prompt_io,
        sample_dir=Path("sample_inputs"),
        tui=tui,
    )
    launcher.run()


if __name__ == "__main__":
    main()
