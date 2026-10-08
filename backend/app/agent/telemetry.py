from collections import Counter
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.core.logs import current_request_id
from app.domain.models import AnalysisReport
from app.domain.requests import ManifestRequest, PackageRequest

RUN_NAME = "package-health-analysis"


def run_config(base: RunnableConfig, request: PackageRequest | ManifestRequest) -> RunnableConfig:
    """Names and tags the run so traces can be filtered, and links it to the request's log lines."""
    tags = [f"mode:{request.mode}"]
    metadata: dict[str, Any] = {"request_id": current_request_id()}
    if isinstance(request, PackageRequest):
        tags.append(f"ecosystem:{request.ecosystem}")
        metadata["package"] = request.package
    else:
        metadata.update(filename=request.filename, include_dev=request.include_dev, content_chars=len(request.content))
    return {**base, "run_name": RUN_NAME, "tags": tags, "metadata": metadata}


def run_summary(report: AnalysisReport, duration_ms: int) -> dict[str, Any]:
    assessments = report.assessments
    upstream_issues = Counter(issue.source for a in assessments for issue in a.signals.issues)
    return {
        "ecosystem": report.ecosystem,
        "manifest": report.manifest,
        "packages": len(assessments),
        "skipped": len(report.skipped),
        "duration_ms": duration_ms,
        "overall": report.overall_verdict.value,
        "verdicts": {verdict.value: count for verdict, count in report.counts.items() if count},
        # Silent fallbacks: rules instead of Jev, templates instead of the LLM.
        "verdict_sources": dict(Counter(a.verdict_source for a in assessments if a.score is not None)),
        "explanation_sources": dict(Counter(a.explanation_source for a in assessments if a.score is not None)),
        "upstream_issues": dict(upstream_issues),
    }
