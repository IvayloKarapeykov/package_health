from datetime import timedelta

import pytest

from app.core.time import utc_now
from app.domain.models import Adoption, DependencyRef, PackageSignals, Severity, Verdict, VulnerabilityReport
from app.services.scoring import HealthScorer, ScoringPolicy, adoption_measure
from tests.factories import healthy_signals, vulnerability

scorer = HealthScorer()


def test_healthy_package_is_recommended() -> None:
    health = scorer.score(healthy_signals())
    assert health.score == 100
    assert health.verdict == Verdict.RECOMMENDED
    assert all(finding.impact == "positive" for finding in health.findings)


def test_missing_package_is_unknown() -> None:
    health = scorer.score(PackageSignals(dependency=DependencyRef(name="nope")))
    assert health.verdict == Verdict.UNKNOWN


def test_deprecation_forces_avoid() -> None:
    signals = healthy_signals()
    signals.registry.deprecated = "Use something else"
    health = scorer.score(signals)
    assert health.verdict == Verdict.AVOID
    assert any(f.impact == "critical" and "Deprecated" in f.message for f in health.findings)


def test_critical_vulnerability_in_latest_forces_avoid() -> None:
    signals = healthy_signals(
        vulnerabilities=VulnerabilityReport(total_known=1, vulnerabilities=[vulnerability(Severity.CRITICAL)])
    )
    assert scorer.score(signals).verdict == Verdict.AVOID


def test_patched_historical_vulnerabilities_count_as_positive() -> None:
    signals = healthy_signals(
        vulnerabilities=VulnerabilityReport(
            total_known=2,
            vulnerabilities=[
                vulnerability(Severity.HIGH, affects_latest=False, id="A"),
                vulnerability(Severity.LOW, affects_latest=False, id="B"),
            ],
        )
    )
    health = scorer.score(signals)
    assert health.score == 100
    assert any("clear of the 2 historical advisories" in f.message for f in health.findings)


def test_stale_and_niche_package_needs_caution() -> None:
    now = utc_now()
    signals = healthy_signals()
    signals.registry.last_release_at = now - timedelta(days=500)
    signals.repository.last_commit_at = now - timedelta(days=400)
    signals.adoption.weekly_downloads = 5_000
    health = scorer.score(signals)
    # 100 - 10 (release) - 8 (commits) - 5 (adoption)
    assert health.score == 77
    assert health.verdict == Verdict.RECOMMENDED

    signals.adoption.weekly_downloads = 200
    signals.repository.stars = 10
    health = scorer.score(signals)
    assert health.verdict == Verdict.CAUTION


@pytest.mark.parametrize(
    ("adoption", "message"),
    [
        (Adoption(weekly_downloads=500), "Very low adoption (500 weekly downloads)"),
        (Adoption(total_downloads=200_000_000), "Widely used (200,000,000 total downloads)"),
        (Adoption(dependents=12), "Modest adoption (12 dependent packages)"),
        (Adoption(weekly_downloads=2_000_000, dependents=3), "Widely used (2,000,000 weekly downloads)"),
    ],
)
def test_adoption_uses_the_best_measure_the_registry_offers(adoption: Adoption, message: str) -> None:
    health = scorer.score(healthy_signals(adoption=adoption))
    assert message in [finding.message for finding in health.findings]


def test_no_adoption_data_is_neutral() -> None:
    health = scorer.score(healthy_signals(adoption=Adoption(note="Go modules publish no download counts")))
    assert health.score == 100


def test_pinned_vulnerable_version_is_called_out() -> None:
    signals = healthy_signals(
        vulnerabilities=VulnerabilityReport(
            total_known=1,
            requested_version="1.0.0",
            requested_pinned=True,
            vulnerabilities=[vulnerability(Severity.HIGH, affects_latest=False).model_copy(update={"affects_requested": True})],
        )
    )
    assert "Your pinned version 1.0.0 has 1 known vulnerability — upgrade" in [f.message for f in scorer.score(signals).findings]


def test_adoption_strength_is_comparable_across_measures() -> None:
    policy = ScoringPolicy()
    popular_weekly = adoption_measure(Adoption(weekly_downloads=2_000_000), policy)
    niche_total = adoption_measure(Adoption(total_downloads=20_000), policy)
    small_dependents = adoption_measure(Adoption(dependents=20), policy)

    assert popular_weekly.strength > small_dependents.strength > niche_total.strength
    assert adoption_measure(Adoption(), policy) is None
