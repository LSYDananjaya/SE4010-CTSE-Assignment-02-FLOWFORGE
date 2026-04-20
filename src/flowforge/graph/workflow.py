from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from flowforge.agents.context_agent import ContextAgent
from flowforge.agents.intake_agent import IntakeAgent
from flowforge.agents.planning_agent import PlanningAgent
from flowforge.agents.qa_agent import QAAgent
from flowforge.graph.nodes import build_agent_node
from flowforge.graph.router import route_after_qa
from flowforge.models.requests import UserRequest
from flowforge.models.state import GraphState, WorkflowState
from flowforge.services.tracing import JsonTraceWriter
from flowforge.tools.intake_parser import IntakeParserTool
from flowforge.tools.qa_validator import QaValidatorTool
from flowforge.tools.repo_context_finder import RepoContextFinderTool
from flowforge.tools.task_plan_builder import TaskPlanBuilderTool


class FlowForgeWorkflow:
    """Main workflow wrapper that runs the LangGraph pipeline."""

    def __init__(
        self,
        *,
        intake_agent: IntakeAgent,
        context_agent: ContextAgent,
        planning_agent: PlanningAgent,
        qa_agent: QAAgent,
        trace_writer: JsonTraceWriter,
    ) -> None:
        self.trace_writer = trace_writer
        graph = StateGraph(GraphState)
        graph.add_node("intake", build_agent_node(name="intake", runner=intake_agent.run, trace_writer=trace_writer))
        graph.add_node("context", build_agent_node(name="context", runner=context_agent.run, trace_writer=trace_writer))
        graph.add_node("planning", build_agent_node(name="planning", runner=planning_agent.run, trace_writer=trace_writer))
        graph.add_node("qa", build_agent_node(name="qa", runner=qa_agent.run, trace_writer=trace_writer))
        graph.add_node("complete", self._complete_node)
        graph.add_edge(START, "intake")
        graph.add_edge("intake", "context")
        graph.add_edge("context", "planning")
        graph.add_edge("planning", "qa")
        graph.add_conditional_edges("qa", route_after_qa, {"complete": "complete"})
        graph.add_edge("complete", END)
        self.graph = graph.compile()

    @staticmethod
    def _complete_node(state: GraphState) -> GraphState:
        """Mark successful completion unless a prior node failed."""
        workflow = state["workflow"]
        if workflow.workflow_status != "failed":
            workflow.workflow_status = "completed"
        return {"workflow": workflow}

    @classmethod
    def from_stub_llm(cls, llm: object, trace_writer: JsonTraceWriter | None = None) -> "FlowForgeWorkflow":
        """Build the workflow with a deterministic test stub."""
        writer = trace_writer or JsonTraceWriter()
        return cls(
            intake_agent=IntakeAgent(llm_client=llm, tool=IntakeParserTool()),
            context_agent=ContextAgent(llm_client=llm, tool=RepoContextFinderTool()),
            planning_agent=PlanningAgent(llm_client=llm, tool=TaskPlanBuilderTool()),
            qa_agent=QAAgent(llm_client=llm, tool=QaValidatorTool()),
            trace_writer=writer,
        )

    @classmethod
    def from_live_llm(
        cls,
        llm_client: object,
        trace_writer: JsonTraceWriter | None = None,
    ) -> "FlowForgeWorkflow":
        """Build the workflow with a live Ollama client."""
        return cls.from_stub_llm(llm=llm_client, trace_writer=trace_writer)

    def run(self, request: UserRequest) -> WorkflowState:
        """Execute the workflow from initial request to final state."""
        state = WorkflowState.initial(request=request)
        result = self.graph.invoke({"workflow": state})
        return result["workflow"]
