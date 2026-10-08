from dataclasses import dataclass

from app.domain.models import Ecosystem


@dataclass(frozen=True)
class EcosystemInfo:
    label: str  # the registry, e.g. "PyPI"
    language: str  # e.g. "Python"

    @property
    def description(self) -> str:
        return f"{self.label} ({self.language})"


ECOSYSTEMS: dict[Ecosystem, EcosystemInfo] = {
    "npm": EcosystemInfo("npm", "JavaScript / TypeScript"),
    "pypi": EcosystemInfo("PyPI", "Python"),
    "maven": EcosystemInfo("Maven Central", "Java / Kotlin"),
    "nuget": EcosystemInfo("NuGet", "C# / .NET"),
    "go": EcosystemInfo("Go modules", "Go"),
    "cargo": EcosystemInfo("crates.io", "Rust"),
    "rubygems": EcosystemInfo("RubyGems", "Ruby"),
    "packagist": EcosystemInfo("Packagist", "PHP"),
}
