from datetime import timedelta

from app.core.time import utc_now
from app.domain.models import (
    Adoption,
    DependencyRef,
    Ecosystem,
    PackageSignals,
    RegistryInfo,
    RepositoryInfo,
    Severity,
    Vulnerability,
    VulnerabilityReport,
)


def healthy_signals(name: str = "healthy-lib", ecosystem: Ecosystem = "npm", **overrides) -> PackageSignals:
    now = utc_now()
    signals = PackageSignals(
        dependency=DependencyRef(name=name, ecosystem=ecosystem, requested="^1.0.0", kind="prod"),
        registry=RegistryInfo(
            latest_version="1.4.0",
            registry_url=f"https://registry.example/{name}",
            license="MIT",
            repository_url=f"git+https://github.com/acme/{name}.git",
            created_at=now - timedelta(days=1500),
            last_release_at=now - timedelta(days=20),
            total_versions=30,
            releases_last_year=6,
            maintainers_count=3,
        ),
        adoption=Adoption(weekly_downloads=2_500_000, note="last 7 days"),
        repository=RepositoryInfo(
            full_name=f"acme/{name}",
            url=f"https://github.com/acme/{name}",
            stars=12_000,
            forks=800,
            open_issues=40,
            archived=False,
            last_commit_at=now - timedelta(days=3),
        ),
        vulnerabilities=VulnerabilityReport(total_known=0),
    )
    return signals.model_copy(update=overrides)


def vulnerability(severity: Severity, *, affects_latest: bool = True, id: str = "GHSA-test") -> Vulnerability:
    return Vulnerability(
        id=id,
        severity=severity,
        url=f"https://osv.dev/vulnerability/{id}",
        affects_latest=affects_latest,
    )
