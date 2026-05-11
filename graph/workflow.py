# graph/workflow.py

from langgraph.graph import StateGraph, END
from models.schemas import AgentState
from agents.cv_parser import cv_parser_agent
from agents.cv_analyzer import cv_analyzer_agent
from agents.job_matcher import job_matcher_agent
from agents.report_builder import report_builder_agent

def cv_parser_node(state: AgentState) -> AgentState:
    # استخدام النقطة للوصول إلى الخصائص بدلاً من الأقواس المربعة
    return cv_parser_agent(state, state.file_path, state.file_name)

def cv_analyzer_node(state: AgentState) -> AgentState:
    return cv_analyzer_agent(state)

def job_matcher_node(state: AgentState) -> AgentState:
    return job_matcher_agent(state)

def report_builder_node(state: AgentState) -> AgentState:
    return report_builder_agent(state)

workflow = StateGraph(AgentState)

workflow.add_node("cv_parser", cv_parser_node)
workflow.add_node("cv_analyzer", cv_analyzer_node)
workflow.add_node("job_matcher", job_matcher_node)
workflow.add_node("report_builder", report_builder_node)

workflow.set_entry_point("cv_parser")
workflow.add_edge("cv_parser", "cv_analyzer")
workflow.add_edge("cv_analyzer", "job_matcher")
workflow.add_edge("job_matcher", "report_builder")
workflow.add_edge("report_builder", END)

graph = workflow.compile()