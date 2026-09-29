"""Domain models shared by the clients, services, agent graph and API.

All models serialize with camelCase keys so the TypeScript frontend can consume them as-is.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        validate_by_alias=True,
        serialize_by_alias=True,
    )


class Verdict(StrEnum):
    RECOMMENDED = "recommended"
    CAUTION = "caution"
    AVOID = "avoid"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    UNKNOWN = "unknown"


# The package ecosystems (registries) the advisor understands.
Ecosystem = Literal["npm", "pypi", "cargo", "go", "maven", "nuget", "rubygems", "packagist"]

DependencyKind = Literal["direct", "prod", "dev", "peer", "optional"]
DataSource = Literal["registry", "adoption", "github", "osv", "llm"]

# The steps one package's assessment walks through, in order.
AssessmentStep = Literal["registry", "activity", "scoring", "deciding", "explaining", "alternatives"]
# Who picked the verdict: the Jev decision model, or the rule-based scorer.
VerdictSource = Literal["jev", "rules"]


# --- Input -----------------------------------------------------------------------------------


class DependencyRef(CamelModel):
    name: str
    ecosystem: Ecosystem = "npm"
    requested: str | None = None
    kind: DependencyKind = "direct"

    @property
    def key(self) -> str:
        """Unique across ecosystems (the same name can exist in several registries)."""
        return f"{self.ecosystem}:{self.name}"


class SkippedDependency(CamelModel):
    name: str
    requested: str
    reason: str


class EcosystemDetection(CamelModel):
    """How an "auto" package request was resolved to a registry."""

    ecosystem: Ecosystem
    # Other registries that publish a package with the same name, most used first.
    also_found_in: list[Ecosystem] = Field(default_factory=list)


# --- Raw signals -----------------------------------------------------------------------------


class RegistryInfo(CamelModel):
    latest_version: str
    registry_url: str
    description: str | None = None
    license: str | None = None
    homepage: str | None = None
    repository_url: str | None = None
    created_at: datetime | None = None
    last_release_at: datetime | None = None
    total_versions: int = 0
    releases_last_year: int = 0
    deprecated: str | None = None
    # Registry-specific extras; None where the registry doesn't expose them.
    maintainers_count: int | None = None
    dependencies_count: int | None = None
    unpacked_size_bytes: int | None = None
    has_types: bool | None = None


class Adoption(CamelModel):
    """How widely a package is used. Registries expose different measures, so all are optional."""

    weekly_downloads: int | None = None
    total_downloads: int | None = None
    dependents: int | None = None
    # e.g. "last 7 days" or "90-day average", so the UI can say where the number came from.
    note: str | None = None


class RepositoryInfo(CamelModel):
    full_name: str
    url: str
    description: str | None = None
    stars: int
    forks: int
    open_issues: int = Field(description="GitHub counts open pull requests as issues too.")
    archived: bool
    last_commit_at: datetime | None = None


class Vulnerability(CamelModel):
    id: str
    summary: str | None = None
    severity: Severity = Severity.UNKNOWN
    aliases: list[str] = []
    url: str
    affects_latest: bool = False
    affects_requested: bool | None = None


class VulnerabilityReport(CamelModel):
    total_known: int
    vulnerabilities: list[Vulnerability] = []
    # The concrete version behind the requested spec, and whether the spec pins it exactly.
    requested_version: str | None = None
    requested_pinned: bool = False

    @property
    def affecting_latest(self) -> list[Vulnerability]:
        return [v for v in self.vulnerabilities if v.affects_latest]

    @property
    def affecting_requested(self) -> list[Vulnerability]:
        return [v for v in self.vulnerabilities if v.affects_requested]


class SourceIssue(CamelModel):
    source: DataSource
    message: str


class PackageSignals(CamelModel):
    dependency: DependencyRef
    registry: RegistryInfo | None = None
    adoption: Adoption | None = None
    repository: RepositoryInfo | None = None
    vulnerabilities: VulnerabilityReport | None = None
    issues: list[SourceIssue] = []

    @property
    def exists(self) -> bool:
        return self.registry is not None


# --- Evaluation ------------------------------------------------------------------------------


class Finding(CamelModel):
    impact: Literal["positive", "negative", "critical"]
    message: str
    penalty: int = 0


class HealthScore(CamelModel):
    score: int = Field(ge=0, le=100)
    verdict: Verdict
    findings: list[Finding] = []


class Alternative(CamelModel):
    name: str
    reason: str
    url: str | None = None
    adoption: Adoption | None = None


class PackageAssessment(CamelModel):
    dependency: DependencyRef
    verdict: Verdict
    score: int | None = None
    summary: str
    reasons: list[str] = []
    findings: list[Finding] = []
    alternatives: list[Alternative] = []
    signals: PackageSignals
    verdict_source: VerdictSource
    verdict_confidence: float | None = None
    explanation_source: Literal["llm", "heuristic"]


class AnalysisReport(CamelModel):
    ecosystem: Ecosystem
    manifest: str | None = None  # detected file format, e.g. "pyproject.toml"; None for a single package
    overall_verdict: Verdict
    summary: str
    counts: dict[Verdict, int]
    assessments: list[PackageAssessment]
    skipped: list[SkippedDependency] = []
    generated_at: datetime
