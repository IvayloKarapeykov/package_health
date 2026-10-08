"""Rule-based health score: 100 minus each finding's penalty. A critical finding forces AVOID."""

import itertools
import math
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime

from app.core.time import days_since, utc_now
from app.domain.models import Adoption, Finding, HealthScore, PackageSignals, Severity, Verdict


@dataclass(frozen=True)
class ScoringPolicy:
    recommended_threshold: int = 75
    caution_threshold: int = 50
    stale_release_days: int = 365
    abandoned_release_days: int = 730
    stale_commit_days: int = 365
    abandoned_commit_days: int = 730
    # Adoption thresholds per measure (registries expose different ones): niche, small, popular.
    weekly_download_levels: tuple[int, int, int] = (1_000, 10_000, 1_000_000)
    total_download_levels: tuple[int, int, int] = (50_000, 1_000_000, 100_000_000)
    dependent_levels: tuple[int, int, int] = (5, 50, 1_000)
    low_star_count: int = 50
    vulnerability_penalties: tuple[tuple[Severity, int], ...] = (
        (Severity.CRITICAL, 40),
        (Severity.HIGH, 25),
        (Severity.MODERATE, 10),
        (Severity.LOW, 5),
        (Severity.UNKNOWN, 10),
    )


Rule = Callable[[PackageSignals, ScoringPolicy, datetime], Iterable[Finding]]


def _negative(message: str, penalty: int) -> Finding:
    return Finding(impact="negative", message=message, penalty=penalty)


def _critical(message: str, penalty: int) -> Finding:
    return Finding(impact="critical", message=message, penalty=penalty)


def _positive(message: str) -> Finding:
    return Finding(impact="positive", message=message)


def _plural(count: int, singular: str, plural: str) -> str:
    return f"{count} {singular if count == 1 else plural}"


def deprecation_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    if signals.registry and signals.registry.deprecated:
        yield _critical(f"Deprecated: “{signals.registry.deprecated}”", 60)


def archived_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    if signals.repository and signals.repository.archived:
        yield _critical("GitHub repository is archived (read-only)", 40)


def vulnerability_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    report = signals.vulnerabilities
    if report is None:
        return
    affecting_latest = report.affecting_latest
    if not affecting_latest:
        if report.total_known:
            advisories = _plural(report.total_known, "historical advisory", "historical advisories")
            yield _positive(f"Latest version is clear of the {advisories}")
        else:
            yield _positive("No known vulnerabilities")
    penalties = dict(policy.vulnerability_penalties)
    for severity in Severity:
        matching = [v for v in affecting_latest if v.severity == severity]
        if not matching:
            continue
        label = f"{severity.value}-severity"
        count = _plural(len(matching), f"{label} vulnerability", f"{label} vulnerabilities")
        message = f"{count} in the latest version"
        if severity == Severity.CRITICAL:
            yield _critical(message, penalties[severity])
        else:
            yield _negative(message, min(penalties[severity] * len(matching), 40))

    affecting_requested = report.affecting_requested
    requested = signals.dependency.requested
    if affecting_requested and requested and report.requested_version:
        count = _plural(len(affecting_requested), "known vulnerability", "known vulnerabilities")
        if report.requested_pinned:
            message = f"Your pinned version {report.requested_version} has {count} — upgrade"
        else:
            message = f"The floor of your range ({requested}) has {count} — raise it to a patched version"
        yield _negative(message, 5)


def release_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    registry = signals.registry
    if registry is None:
        return
    age = days_since(registry.last_release_at, now)
    if age is None:
        return
    if age > policy.abandoned_release_days:
        yield _negative(f"No release in {round(age / 365)} years", 20)
    elif age > policy.stale_release_days:
        yield _negative("No release in over a year", 10)
    elif registry.releases_last_year >= 2:
        yield _positive(f"{registry.releases_last_year} releases in the last 12 months")


def activity_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    repository = signals.repository
    if repository is None:
        return
    age = days_since(repository.last_commit_at, now)
    if age is None:
        return
    if age > policy.abandoned_commit_days:
        yield _negative(f"Last commit was {round(age / 365)} years ago", 15)
    elif age > policy.stale_commit_days:
        yield _negative("No commits in over a year", 8)
    elif age <= 30:
        yield _positive("Actively developed (commit in the last 30 days)")


@dataclass(frozen=True)
class AdoptionMeasure:
    value: int
    unit: str  # e.g. "weekly downloads"
    levels: tuple[int, int, int]  # niche, small, popular

    @property
    def strength(self) -> float:
        """0 (unused) to 4 (far past "popular"), log-interpolated between the levels.

        Comparable across registries even though each exposes a different measure.
        """
        bounds = (1, *self.levels)
        for tier, (low, high) in enumerate(itertools.pairwise(bounds)):
            if self.value < high:
                return tier + (math.log(max(self.value, 1) / low) / math.log(high / low) if self.value >= low else 0)
        return len(self.levels) + min(math.log10(self.value / bounds[-1]) / 3, 0.99)


def adoption_measure(adoption: Adoption | None, policy: ScoringPolicy) -> AdoptionMeasure | None:
    """The best measure the registry offers: recent downloads, then lifetime downloads, then dependents."""
    if adoption is None:
        return None
    if adoption.weekly_downloads is not None:
        return AdoptionMeasure(adoption.weekly_downloads, "weekly downloads", policy.weekly_download_levels)
    if adoption.total_downloads is not None:
        return AdoptionMeasure(adoption.total_downloads, "total downloads", policy.total_download_levels)
    if adoption.dependents is not None:
        return AdoptionMeasure(adoption.dependents, "dependent packages", policy.dependent_levels)
    return None


def adoption_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    if measure := adoption_measure(signals.adoption, policy):
        niche, small, popular = measure.levels
        value, unit = measure.value, measure.unit
        if value < niche:
            yield _negative(f"Very low adoption ({value:,} {unit})", 15)
        elif value < small:
            yield _negative(f"Modest adoption ({value:,} {unit})", 5)
        elif value >= popular:
            yield _positive(f"Widely used ({value:,} {unit})")
    if signals.repository is not None and signals.repository.stars < policy.low_star_count:
        yield _negative(f"Small community ({signals.repository.stars} GitHub stars)", 5)


def provenance_rule(signals: PackageSignals, policy: ScoringPolicy, now: datetime) -> Iterable[Finding]:
    registry = signals.registry
    if registry is None:
        return
    if not registry.repository_url:
        yield _negative("No source repository listed", 10)
    if not registry.license:
        yield _negative("No license declared", 10)


DEFAULT_RULES: tuple[Rule, ...] = (
    deprecation_rule,
    archived_rule,
    vulnerability_rule,
    release_rule,
    activity_rule,
    adoption_rule,
    provenance_rule,
)


class HealthScorer:
    def __init__(self, policy: ScoringPolicy | None = None, rules: tuple[Rule, ...] = DEFAULT_RULES) -> None:
        self._policy = policy or ScoringPolicy()
        self._rules = rules

    def score(self, signals: PackageSignals, now: datetime | None = None) -> HealthScore:
        if not signals.exists:
            return HealthScore(score=0, verdict=Verdict.UNKNOWN, findings=[])

        now = now or utc_now()
        findings = [finding for rule in self._rules for finding in rule(signals, self._policy, now)]
        score = max(0, 100 - sum(finding.penalty for finding in findings))
        return HealthScore(score=score, verdict=self._verdict(score, findings), findings=findings)

    def _verdict(self, score: int, findings: list[Finding]) -> Verdict:
        if any(finding.impact == "critical" for finding in findings):
            return Verdict.AVOID
        if score >= self._policy.recommended_threshold:
            return Verdict.RECOMMENDED
        if score >= self._policy.caution_threshold:
            return Verdict.CAUTION
        return Verdict.AVOID
