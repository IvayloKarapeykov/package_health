import functools
import logging
from collections.abc import Awaitable, Callable
from typing import cast

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agent.services import AgentServices
from app.agent.state import PackageInput, PackageOutput, PackageState, PackageUpdate
from app.domain.models import AssessmentStep, PackageAssessment, PackageSignals, SourceIssue, Verdict

logger = logging.getLogger(__name__)

COLLECT = "collect"
SCORE = "score"
DECIDE = "decide"
EXPLAIN = "explain"
VERIFY_ALTERNATIVES = "verify_alternatives"
FINALIZE = "finalize"

Node = Callable[["PackageNodes", PackageState], Awaitable[PackageUpdate]]


def report_step(dependency_key: str, step: AssessmentStep) -> None:
    """Publish a package's current step on LangGraph's "custom" stream (a no-op when not streamed)."""
    get_stream_writer()({"dependency_key": dependency_key, "step": step})


def guarded[N: Node](node: N) -> N:
    """Skip the node after an earlier failure, and turn a crash into state instead of an exception,
    so one broken package never sinks the whole report. Keeps the node's signature for type checkers."""

    @functools.wraps(node)
    async def wrapper(self: "PackageNodes", state: PackageState) -> PackageUpdate:
        if state.get("error"):
            return {}
        try:
            return await node(self, state)
        except Exception:
            logger.exception("%s crashed for %s", node.__name__, state["dependency"].key)
            return {"error": f"Unexpected error while running '{node.__name__}'"}

    return cast(N, wrapper)


class PackageNodes:
    def __init__(self, services: AgentServices) -> None:
        self._s = services

    @guarded
    async def collect(self, state: PackageState) -> PackageUpdate:
        dependency = state["dependency"]
        signals = await self._s.collector.collect(dependency, on_stage=lambda step: report_step(dependency.key, step))
        return {"signals": signals}

    @guarded
    async def score(self, state: PackageState) -> PackageUpdate:
        report_step(state["dependency"].key, "scoring")
        return {"health": self._s.scorer.score(state["signals"])}

    @guarded
    async def decide(self, state: PackageState) -> PackageUpdate:
        report_step(state["dependency"].key, "deciding")
        return {"decision": await self._s.decider.decide(state["signals"], state["health"])}

    @guarded
    async def explain(self, state: PackageState) -> PackageUpdate:
        report_step(state["dependency"].key, "explaining")
        explanation = await self._s.explainer.explain(state["signals"], state["health"], state["decision"].verdict)
        return {"explanation": explanation}

    @guarded
    async def verify_alternatives(self, state: PackageState) -> PackageUpdate:
        report_step(state["dependency"].key, "alternatives")
        suggestions = state["explanation"].alternatives
        return {"alternatives": await self._s.alternatives.verify(state["dependency"], suggestions)}

    async def finalize(self, state: PackageState) -> PackageUpdate:
        return {"assessments": [build_assessment(state)]}


    @staticmethod
    def after_collect(state: PackageState) -> str:
        found = not state.get("error") and state["signals"].exists
        return SCORE if found else FINALIZE

    @staticmethod
    def after_explain(state: PackageState) -> str:
        if state.get("error") or not state["explanation"].alternatives:
            return FINALIZE
        return VERIFY_ALTERNATIVES


def build_assessment(state: PackageState) -> PackageAssessment:
    dependency = state["dependency"]
    signals = state.get("signals") or PackageSignals(dependency=dependency)

    if error := state.get("error"):
        return PackageAssessment(
            dependency=dependency,
            verdict=Verdict.UNKNOWN,
            summary="The analysis failed unexpectedly for this package.",
            signals=signals.model_copy(update={"issues": [*signals.issues, SourceIssue(source="registry", message=error)]}),
            verdict_source="rules",
            explanation_source="heuristic",
        )
    if not signals.exists:
        return PackageAssessment(
            dependency=dependency,
            verdict=Verdict.UNKNOWN,
            summary=f"“{dependency.name}” was not found on its registry.",
            reasons=[issue.message for issue in signals.issues if issue.source == "registry"],
            signals=signals,
            verdict_source="rules",
            explanation_source="heuristic",
        )

    health, decision, explanation = state["health"], state["decision"], state["explanation"]
    return PackageAssessment(
        dependency=dependency,
        verdict=decision.verdict,
        verdict_source=decision.source,
        verdict_confidence=decision.confidence,
        score=health.score,
        summary=explanation.summary,
        reasons=explanation.reasons,
        findings=health.findings,
        alternatives=state.get("alternatives") or [],
        signals=signals,
        explanation_source=explanation.source,
    )


def build_package_graph(services: AgentServices) -> CompiledStateGraph:
    nodes = PackageNodes(services)

    graph = StateGraph(PackageState, input_schema=PackageInput, output_schema=PackageOutput)
    graph.add_node(COLLECT, nodes.collect)
    graph.add_node(SCORE, nodes.score)
    graph.add_node(DECIDE, nodes.decide)
    graph.add_node(EXPLAIN, nodes.explain)
    graph.add_node(VERIFY_ALTERNATIVES, nodes.verify_alternatives)
    graph.add_node(FINALIZE, nodes.finalize)

    graph.add_edge(START, COLLECT)
    graph.add_conditional_edges(COLLECT, nodes.after_collect, [SCORE, FINALIZE])
    graph.add_edge(SCORE, DECIDE)
    graph.add_edge(DECIDE, EXPLAIN)
    graph.add_conditional_edges(EXPLAIN, nodes.after_explain, [VERIFY_ALTERNATIVES, FINALIZE])
    graph.add_edge(VERIFY_ALTERNATIVES, FINALIZE)
    graph.add_edge(FINALIZE, END)

    return graph.compile(name="assess-package")
