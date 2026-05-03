from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from flowforge.models.state import GraphState, WorkflowState
from flowforge.services.tracing import JsonTraceWriter


def build_agent_node(
    *,
    name: str,
    runner: Callable[[WorkflowState], WorkflowState],
    trace_writer: JsonTraceWriter,
) -> Callable[[GraphState], GraphState]:
    """Wrap an agent runner with trace emission."""

    def node(state: GraphState) -> GraphState:
        workflow = state["workflow"]
        started = perf_counter()
        trace_writer.write_event(
            run_id=workflow.run_id,
            node_name=name,
            status="started",
            latency_ms=0.0,
            detail="",
        )
        status = "success"
        error_message = ""
        try:
            workflow = runner(workflow)
        except Exception as exc:  # noqa: BLE001
            workflow.workflow_status = "failed"
            trace_context = workflow.trace_context.get(name, {})
            error_message = str(trace_context.get("failure_cause", "")) or str(exc)
            workflow.errors.append(error_message)
            workflow.errors.append(f"{name.title()} Agent failed.")
            status = "error"
        trace_context = workflow.trace_context.get(name, {})
        trace_writer.write_event(
            run_id=workflow.run_id,
            node_name=name,
            status=status,
            latency_ms=(perf_counter() - started) * 1000,
            detail=error_message,
            agent_input_summary=str(trace_context.get("agent_input_summary", "")),
            tool_name=str(trace_context.get("tool_name", "")),
            tool_input_summary=str(trace_context.get("tool_input_summary", "")),
            tool_output_summary=str(trace_context.get("tool_output_summary", "")),
            fallback_used=bool(trace_context.get("fallback_used", False)),
            llm_output_summary=str(trace_context.get("llm_output_summary", "")),
            failure_cause=error_message or str(trace_context.get("failure_cause", "")),
        )
        workflow.trace_file = trace_writer.trace_path_for(workflow.run_id)
        return {"workflow": workflow}

    return node
