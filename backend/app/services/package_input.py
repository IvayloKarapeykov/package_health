"""Turns user input (one package, or a dependency manifest) into dependencies to analyze."""

from dataclasses import dataclass, field

from app.domain.errors import InvalidInputError
from app.domain.models import DependencyRef, Ecosystem, SkippedDependency
from app.ecosystems.registry import EcosystemRegistry
from app.manifests.base import ManifestEntries
from app.manifests.registry import find_parser


@dataclass
class ParsedInput:
    ecosystem: Ecosystem
    manifest: str | None = None  # the detected file format, e.g. "pyproject.toml"
    dependencies: list[DependencyRef] = field(default_factory=list)
    skipped: list[SkippedDependency] = field(default_factory=list)


class DependencyInputParser:
    def __init__(self, ecosystems: EcosystemRegistry, max_packages: int) -> None:
        self._ecosystems = ecosystems
        self._max_packages = max_packages

    def parse_package(self, raw: str, ecosystem: Ecosystem) -> ParsedInput:
        """Parse a single package spec, e.g. `express@4`, `requests>=2.31`, `org.slf4j:slf4j-api:2.0.9`."""
        adapter = self._ecosystems.get(ecosystem)
        name, requested = adapter.split_spec(raw)
        name = adapter.normalize_name(name)
        if not adapter.is_valid_name(name):
            raise InvalidInputError(f"'{raw.strip()}' is not a valid {adapter.label} package name.")
        return ParsedInput(
            ecosystem=ecosystem,
            dependencies=[DependencyRef(name=name, ecosystem=ecosystem, requested=requested, kind="direct")],
        )

    def parse_manifest(self, content: str, *, filename: str | None, include_dev: bool) -> ParsedInput:
        parser = find_parser(content, filename)
        entries = parser.parse(content, include_dev=include_dev)
        if not entries.dependencies and not entries.skipped:
            raise InvalidInputError(f"No dependencies found in this {parser.format}.")
        result = self._normalize(entries, parser.ecosystem)
        result.manifest = parser.format
        return result

    def _normalize(self, entries: ManifestEntries, ecosystem: Ecosystem) -> ParsedInput:
        adapter = self._ecosystems.get(ecosystem)
        result = ParsedInput(ecosystem=ecosystem)
        seen: set[str] = set()
        for skip in entries.skipped:
            result.skipped.append(SkippedDependency(name=skip.name, requested=skip.requested, reason=skip.reason))
        for entry in entries.dependencies:
            name = adapter.normalize_name(entry.name)
            if name in seen:  # the first section a package appears in wins
                continue
            seen.add(name)
            if not adapter.is_valid_name(name):
                result.skipped.append(
                    SkippedDependency(name=entry.name, requested=entry.requested or "", reason="Invalid package name")
                )
                continue
            dependency = DependencyRef(name=name, ecosystem=ecosystem, requested=entry.requested, kind=entry.kind)
            if len(result.dependencies) < self._max_packages:
                result.dependencies.append(dependency)
            else:
                result.skipped.append(
                    SkippedDependency(
                        name=name,
                        requested=entry.requested or "",
                        reason=f"Analysis limit of {self._max_packages} packages reached",
                    )
                )
        return result
