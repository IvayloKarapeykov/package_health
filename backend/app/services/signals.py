import asyncio
from collections.abc import Awaitable, Callable
from typing import Protocol

from app.clients.github import GitHubClient, parse_github_repository
from app.clients.osv import OsvClient
from app.core.http import NotFoundError, UpstreamError
from app.domain.models import (
    AssessmentStep,
    DataSource,
    DependencyRef,
    PackageSignals,
    RepositoryInfo,
    SourceIssue,
    VulnerabilityReport,
)
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.registry import EcosystemRegistry

StageCallback = Callable[[AssessmentStep], None]


class SignalSource(Protocol):
    async def collect(self, dependency: DependencyRef, on_stage: StageCallback | None = None) -> PackageSignals: ...


class SignalCollector:
    def __init__(self, ecosystems: EcosystemRegistry, github: GitHubClient, osv: OsvClient) -> None:
        self._ecosystems = ecosystems
        self._github = github
        self._osv = osv

    async def collect(self, dependency: DependencyRef, on_stage: StageCallback | None = None) -> PackageSignals:
        report = on_stage or (lambda _step: None)
        adapter = self._ecosystems.get(dependency.ecosystem)
        signals = PackageSignals(dependency=dependency)

        # Stage 1: registry metadata + adoption (the registry tells us where the repo lives).
        report("registry")
        signals.registry, signals.adoption = await asyncio.gather(
            self._attempt(signals, "registry", adapter.get_package(dependency.name)),
            self._attempt(signals, "adoption", adapter.get_adoption(dependency.name)),
        )
        if signals.registry is None:
            return signals

        # Stage 2: GitHub activity + known vulnerabilities.
        report("activity")
        signals.repository, signals.vulnerabilities = await asyncio.gather(
            self._attempt(signals, "github", self._repository(signals)),
            self._attempt(signals, "osv", self._vulnerabilities(signals, adapter)),
        )
        return signals

    async def _repository(self, signals: PackageSignals) -> RepositoryInfo | None:
        assert signals.registry is not None
        coordinates = parse_github_repository(signals.registry.repository_url) or parse_github_repository(
            signals.registry.homepage
        )
        if coordinates is None:
            signals.issues.append(SourceIssue(source="github", message="No GitHub repository linked in package metadata"))
            return None
        return await self._github.get_repository(*coordinates)

    async def _vulnerabilities(self, signals: PackageSignals, adapter: EcosystemAdapter) -> VulnerabilityReport:
        assert signals.registry is not None
        name = signals.dependency.name
        latest = signals.registry.latest_version
        spec = adapter.version_spec(signals.dependency.requested)
        requested = spec.version
        check_requested = requested is not None and requested != latest

        all_known, in_latest, in_requested = await asyncio.gather(
            self._osv.query(adapter.osv_ecosystem, name),
            self._osv.query(adapter.osv_ecosystem, name, latest),
            self._osv.query(adapter.osv_ecosystem, name, requested) if check_requested else _none(),
        )
        latest_ids = {v.id for v in in_latest}
        requested_ids = {v.id for v in in_requested} if in_requested is not None else latest_ids
        known = {v.id: v for v in [*all_known, *in_latest, *(in_requested or [])]}

        return VulnerabilityReport(
            total_known=len(known),
            requested_version=requested,
            requested_pinned=spec.pinned,
            vulnerabilities=[
                v.model_copy(
                    update={
                        "affects_latest": v.id in latest_ids,
                        "affects_requested": v.id in requested_ids if requested else None,
                    }
                )
                for v in known.values()
            ],
        )

    @staticmethod
    async def _attempt[T](signals: PackageSignals, source: DataSource, work: Awaitable[T]) -> T | None:
        """Run one source lookup; record a failure on `signals` instead of failing the package."""
        try:
            return await work
        except NotFoundError:
            message = "Package not found on its registry" if source == "registry" else "Not found"
            signals.issues.append(SourceIssue(source=source, message=message))
        except UpstreamError as exc:
            signals.issues.append(SourceIssue(source=source, message=exc.message))
        return None


async def _none() -> None:
    return None
