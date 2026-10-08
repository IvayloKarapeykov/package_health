from typing import Literal

from app.domain.models import (
    AnalysisReport,
    AssessmentStep,
    CamelModel,
    DependencyRef,
    Ecosystem,
    EcosystemDetection,
    PackageAssessment,
    SkippedDependency,
)


class PlanEvent(CamelModel):
    type: Literal["plan"] = "plan"
    ecosystem: Ecosystem
    manifest: str | None = None
    detection: EcosystemDetection | None = None  # set for an auto-detected single package
    dependencies: list[DependencyRef]
    skipped: list[SkippedDependency]


class ProgressEvent(CamelModel):
    """A branch moved on to its next step (emitted via LangGraph's custom stream)."""

    type: Literal["progress"] = "progress"
    dependency_key: str  # DependencyRef.key, e.g. "pypi:requests"
    step: AssessmentStep


class AssessmentEvent(CamelModel):
    type: Literal["assessment"] = "assessment"
    assessment: PackageAssessment


class ReportEvent(CamelModel):
    type: Literal["report"] = "report"
    report: AnalysisReport


class ErrorEvent(CamelModel):
    type: Literal["error"] = "error"
    # invalid_input: the user can fix it; internal: something failed on our side.
    kind: Literal["invalid_input", "internal"]
    message: str
    # Quote this when reporting a problem: it appears on every log line and trace of the request.
    request_id: str | None = None


AnalysisEvent = PlanEvent | ProgressEvent | AssessmentEvent | ReportEvent | ErrorEvent
