"""The package-health graph: a map-reduce over dependencies using LangGraph's Send API.

    START → parse_input ─┬─ Send → [assess_package subgraph] ─┐
                         ├─ Send → [assess_package subgraph] ─┼→ compile_report → END
                         └─ Send → [assess_package subgraph] ─┘

Each `assess_package` is the per-package subgraph in `package_graph.py`.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.nodes import ASSESS_PACKAGE, COMPILE_REPORT, PARSE_INPUT, AnalysisNodes
from app.agent.package_graph import build_package_graph
from app.agent.services import AgentServices
from app.agent.state import AnalysisState


def build_graph(services: AgentServices) -> CompiledStateGraph:
    nodes = AnalysisNodes(services)

    graph = StateGraph(AnalysisState)
    graph.add_node(PARSE_INPUT, nodes.parse_input)
    graph.add_node(ASSESS_PACKAGE, build_package_graph(services))
    graph.add_node(COMPILE_REPORT, nodes.compile_report)

    graph.add_edge(START, PARSE_INPUT)
    graph.add_conditional_edges(PARSE_INPUT, nodes.fan_out, [ASSESS_PACKAGE, COMPILE_REPORT])
    graph.add_edge(ASSESS_PACKAGE, COMPILE_REPORT)
    graph.add_edge(COMPILE_REPORT, END)

    return graph.compile(name="package-health-advisor")
