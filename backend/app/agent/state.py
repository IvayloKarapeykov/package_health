import operator
from typing import Annotated, TypedDict

from app.domain.models import (
    Alternative,
    AnalysisReport,
    DependencyRef,
    Ecosystem,
    EcosystemDetection,
    HealthScore,
    PackageAssessment,
    PackageSignals,
    SkippedDependency,
)
from app.domain.requests import ManifestRequest, PackageRequest
from app.services.advice import Explanation, VerdictDecision


class AnalysisState(TypedDict, total=False):
    request: PackageRequest | ManifestRequest | dict
    ecosystem: Ecosystem
    manifest: str | None  # detected file format, e.g. "pyproject.toml"
    detection: EcosystemDetection | None  # set when a single package's ecosystem was auto-detected
    dependencies: list[DependencyRef]
    skipped: list[SkippedDependency]
    # Each package subgraph appends its assessment.
    assessments: Annotated[list[PackageAssessment], operator.add]
    report: AnalysisReport


class PackageInput(TypedDict):
    """What `Send` hands each package subgraph."""

    dependency: DependencyRef


class PackageOutput(TypedDict):
    """What each package subgraph returns to the main graph (merged by its reducer)."""

    assessments: list[PackageAssessment]


class PackageUpdate(TypedDict, total=False):
    signals: PackageSignals
    health: HealthScore
    decision: VerdictDecision
    explanation: Explanation
    alternatives: list[Alternative]
    error: str  # set when a step crashed; later steps are skipped and the package is reported as failed
    assessments: list[PackageAssessment]


class PackageState(PackageInput, PackageUpdate):
    """The subgraph's full state: the dependency it was sent, plus everything its nodes produced."""
