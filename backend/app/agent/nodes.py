from collections import Counter

from langgraph.types import Send
from pydantic import TypeAdapter, ValidationError

from app.agent.services import AgentServices
from app.agent.state import AnalysisState, PackageInput
from app.core.time import utc_now
from app.domain.errors import InvalidInputError
from app.domain.models import AnalysisReport, PackageAssessment, Verdict
from app.domain.requests import AUTO_DETECT, AnalysisRequest, PackageRequest

PARSE_INPUT = "parse_input"
ASSESS_PACKAGE = "assess_package"
COMPILE_REPORT = "compile_report"

# Worst first: used for both ordering the report and deriving the overall verdict.
VERDICT_SEVERITY = {Verdict.AVOID: 0, Verdict.CAUTION: 1, Verdict.RECOMMENDED: 2, Verdict.UNKNOWN: 3}

_request_adapter: TypeAdapter[AnalysisRequest] = TypeAdapter(AnalysisRequest)


class AnalysisNodes:
    def __init__(self, services: AgentServices) -> None:
        self._s = services

    async def parse_input(self, state: AnalysisState) -> AnalysisState:
        # Accepts a model (FastAPI) or raw JSON (LangGraph Studio / API server).
        try:
            request = _request_adapter.validate_python(state.get("request"))
        except ValidationError as exc:
            raise InvalidInputError(f"Invalid request: {exc.errors()[0]['msg']}") from exc

        detection = None
        if isinstance(request, PackageRequest):
            ecosystem = request.ecosystem
            if ecosystem == AUTO_DETECT:
                detection = await self._s.detector.detect(request.package)
                ecosystem = detection.ecosystem
            parsed = self._s.input_parser.parse_package(request.package, ecosystem)
        else:
            parsed = self._s.input_parser.parse_manifest(
                request.content, filename=request.filename, include_dev=request.include_dev
            )
        return {
            "ecosystem": parsed.ecosystem,
            "manifest": parsed.manifest,
            "detection": detection,
            "dependencies": parsed.dependencies,
            "skipped": parsed.skipped,
        }

    @staticmethod
    def fan_out(state: AnalysisState) -> list[Send] | str:
        dependencies = state.get("dependencies") or []
        if not dependencies:
            return COMPILE_REPORT
        return [Send(ASSESS_PACKAGE, PackageInput(dependency=dependency)) for dependency in dependencies]

    async def compile_report(self, state: AnalysisState) -> AnalysisState:
        order = {dep.key: index for index, dep in enumerate(state.get("dependencies") or [])}
        assessments = sorted(
            state.get("assessments") or [],
            key=lambda a: (VERDICT_SEVERITY[a.verdict], order.get(a.dependency.key, 0)),
        )
        counts = Counter(assessment.verdict for assessment in assessments)
        summary = (
            await self._s.explainer.summarize(assessments)
            if assessments
            else "Nothing to analyze: every dependency was skipped."
        )
        report = AnalysisReport(
            ecosystem=state["ecosystem"],
            manifest=state.get("manifest"),
            overall_verdict=_overall_verdict(assessments),
            summary=summary,
            counts={verdict: counts.get(verdict, 0) for verdict in Verdict},
            assessments=assessments,
            skipped=state.get("skipped") or [],
            generated_at=utc_now(),
        )
        return {"report": report}


def _overall_verdict(assessments: list[PackageAssessment]) -> Verdict:
    known = [a.verdict for a in assessments if a.verdict != Verdict.UNKNOWN]
    if not known:
        return Verdict.UNKNOWN
    return min(known, key=VERDICT_SEVERITY.__getitem__)
