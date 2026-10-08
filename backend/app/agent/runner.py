import logging
import time
from collections.abc import AsyncIterator
from typing import Any, cast

from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from app.agent.nodes import ASSESS_PACKAGE, COMPILE_REPORT, PARSE_INPUT
from app.agent.telemetry import run_config, run_summary
from app.core.logs import current_request_id, fields
from app.domain.errors import InvalidInputError
from app.domain.events import (
    AnalysisEvent,
    AssessmentEvent,
    ErrorEvent,
    PlanEvent,
    ProgressEvent,
    ReportEvent,
)
from app.domain.models import AnalysisReport
from app.domain.requests import ManifestRequest, PackageRequest

logger = logging.getLogger(__name__)


class AnalysisRunner:
    def __init__(self, graph: CompiledStateGraph, max_concurrency: int) -> None:
        self._graph = graph
        self._config: RunnableConfig = {"max_concurrency": max_concurrency}

    async def stream(self, request: PackageRequest | ManifestRequest) -> AsyncIterator[AnalysisEvent]:
        started = time.perf_counter()
        outcome = "cancelled"  # unless the stream ends on its own: the client went away mid-analysis
        try:
            # "updates": node results (plan, assessments, report); "custom": per-package step progress.
            # subgraphs=True surfaces the custom events emitted inside each package subgraph.
            async for namespace, mode, chunk in self._graph.astream(
                {"request": request},
                config=run_config(self._config, request),
                stream_mode=["updates", "custom"],
                subgraphs=True,
            ):
                if mode == "custom":
                    yield ProgressEvent.model_validate(chunk)
                    continue
                if namespace:  # a subgraph's internal node updates; the parent reports the merged result
                    continue
                for node, output in cast(dict[str, Any], chunk).items():
                    if event := _to_event(node, output or {}):
                        if isinstance(event, ReportEvent):
                            outcome = "finished"
                            _log_finished(event.report, started)
                        yield event
        except InvalidInputError as exc:
            outcome = "rejected"
            logger.info("Analysis rejected", extra=fields(mode=request.mode, reason=str(exc)))
            yield ErrorEvent(kind="invalid_input", message=str(exc), request_id=current_request_id())
        except Exception:
            outcome = "failed"
            logger.exception("Analysis failed", extra=fields(mode=request.mode, duration_ms=_ms(started)))
            yield ErrorEvent(
                kind="internal",
                message="The analysis failed unexpectedly. Please try again.",
                request_id=current_request_id(),
            )
        finally:
            if outcome == "cancelled":
                logger.info("Analysis cancelled by the client", extra=fields(duration_ms=_ms(started)))

    async def run(self, request: PackageRequest | ManifestRequest) -> AnalysisReport:
        """Raises InvalidInputError for bad input."""
        started = time.perf_counter()
        final_state = await self._graph.ainvoke({"request": request}, config=run_config(self._config, request))
        report: AnalysisReport = final_state["report"]
        _log_finished(report, started)
        return report


def _log_finished(report: AnalysisReport, started: float) -> None:
    summary = run_summary(report, _ms(started))
    logger.info("Analysis finished", extra=fields(**summary))


def _ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def _to_event(node: str, output: dict) -> AnalysisEvent | None:
    if node == PARSE_INPUT:
        return PlanEvent(
            ecosystem=output["ecosystem"],
            manifest=output["manifest"],
            detection=output.get("detection"),
            dependencies=output["dependencies"],
            skipped=output["skipped"],
        )
    if node == ASSESS_PACKAGE:
        return AssessmentEvent(assessment=output["assessments"][0])
    if node == COMPILE_REPORT:
        return ReportEvent(report=output["report"])
    return None
