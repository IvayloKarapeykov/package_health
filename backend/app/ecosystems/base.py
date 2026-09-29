"""The adapter contract every package ecosystem implements.

Everything ecosystem-specific (where metadata and adoption come from, how names and version
specs look) lives behind this interface; the graph, scoring, Jev and the LLM stay generic.
"""

import re
from abc import ABC, abstractmethod

from app.core.http import NotFoundError
from app.domain.ecosystems import ECOSYSTEMS
from app.domain.models import Adoption, Ecosystem, RegistryInfo
from app.ecosystems.versions import VersionSpec, parse_version_spec


class EcosystemAdapter(ABC):
    id: Ecosystem
    osv_ecosystem: str  # OSV.dev's ecosystem name
    # Whether a bare version ("1.2.3") pins exactly (npm) or means a compatible range (Cargo).
    bare_version_is_exact: bool = True
    name_pattern: re.Pattern[str]

    @property
    def label(self) -> str:
        return ECOSYSTEMS[self.id].label

    @abstractmethod
    async def get_package(self, name: str) -> RegistryInfo:
        """Registry metadata for `name`. Raises NotFoundError if it doesn't exist."""

    @abstractmethod
    async def get_adoption(self, name: str) -> Adoption:
        """Usage signals for `name` (downloads and/or dependents)."""

    @abstractmethod
    def package_url(self, name: str) -> str:
        """The package's page on its registry website."""

    def normalize_name(self, raw: str) -> str:
        return raw.strip()

    def is_valid_name(self, name: str) -> bool:
        return len(name) <= 214 and bool(self.name_pattern.match(name))

    def split_spec(self, raw: str) -> tuple[str, str | None]:
        """Split user input like `name@1.2.3` into (name, requested version spec)."""
        spec = raw.strip()
        at = spec.rfind("@")
        if at > 0:
            return spec[:at], spec[at + 1 :] or None
        return spec, None

    def version_spec(self, requested: str | None) -> VersionSpec:
        return parse_version_spec(requested, bare_is_exact=self.bare_version_is_exact)

    async def exists(self, name: str) -> bool:
        try:
            await self.get_package(name)
        except NotFoundError:
            return False
        return True
