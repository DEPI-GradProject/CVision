import logging

from langgraph.graph import END, StateGraph

from agents.cv_analyzer import cv_analyzer_agent
from agents.cv_parser import cv_parser_agent
from agents.job_matcher import job_matcher_agent
from agents.report_builder import report_builder_agent
from models.schemas import AgentState

logger = logging.getLogger(__name__)


def cv_parser_node(state: AgentState) -> AgentState:
    return cv_parser_agent(state, state.file_path, state.file_name)


def cv_analyzer_node(state: AgentState) -> AgentState:
    return cv_analyzer_agent(state)


def job_matcher_node(state: AgentState) -> AgentState:
    return job_matcher_agent(state)


def report_builder_node(state: AgentState) -> AgentState:
    return report_builder_agent(state)


def should_continue(state: AgentState) -> str:
    if state.error:
        logger.warning("Pipeline halted at error: %s", state.error)
        return "end"
    return "continue"


workflow = StateGraph(AgentState)

workflow.add_node("cv_parser", cv_parser_node)
workflow.add_node("cv_analyzer", cv_analyzer_node)
workflow.add_node("job_matcher", job_matcher_node)
workflow.add_node("report_builder", report_builder_node)

workflow.set_entry_point("cv_parser")

workflow.add_conditional_edges("cv_parser", should_continue, {"continue": "cv_analyzer", "end": END})
workflow.add_conditional_edges("cv_analyzer", should_continue, {"continue": "job_matcher", "end": END})
workflow.add_conditional_edges("job_matcher", should_continue, {"continue": "report_builder", "end": END})
workflow.add_edge("report_builder", END)

graph = workflow.compile()
