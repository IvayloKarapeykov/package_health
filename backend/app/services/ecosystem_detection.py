"""Works out which registry a bare package spec belongs to ("auto" ecosystem).

1. Syntax narrows the field: each adapter only accepts names that fit its rules, so
   `@scope/pkg` can only be npm, `group:artifact` only Maven, `vendor/pkg` only Packagist and
   `github.com/owner/repo` only Go.
2. Plain names (`requests`, `serde`, `rails`) are looked up in every remaining registry at once.
3. When several registries publish the name, the one where it is most used wins. Adoption
   strength is comparable across registries even though each exposes a different measure.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

from app.core.http import UpstreamError
from app.domain.ecosystems import ECOSYSTEMS
from app.domain.errors import InvalidInputError
from app.domain.models import Ecosystem, EcosystemDetection
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.registry import EcosystemRegistry
from app.services.scoring import ScoringPolicy, adoption_measure

logger = logging.getLogger(__name__)

# Tie-break for equally used packages: the order of the ecosystems table (most used registries first).
_PREFERENCE = {ecosystem: index for index, ecosystem in enumerate(ECOSYSTEMS)}


class EcosystemResolver(Protocol):
    async def detect(self, raw: str) -> EcosystemDetection: ...


@dataclass(frozen=True)
class _Match:
    ecosystem: Ecosystem
    strength: float


class EcosystemDetector:
    def __init__(self, ecosystems: EcosystemRegistry, policy: ScoringPolicy | None = None) -> None:
        self._ecosystems = ecosystems
        self._policy = policy or ScoringPolicy()

    async def detect(self, raw: str) -> EcosystemDetection:
        candidates = [adapter for adapter in self._ecosystems.all() if _fits(adapter, raw)]
        if not candidates:
            raise InvalidInputError(f"'{raw.strip()}' doesn't look like a package name in any supported ecosystem.")
        if len(candidates) == 1:  # the syntax alone decides; the analysis reports it if it doesn't exist
            return EcosystemDetection(ecosystem=candidates[0].id)

        probes = await asyncio.gather(*(self._probe(adapter, raw) for adapter in candidates))
        matches = sorted(
            (match for match in probes if match is not None),
            key=lambda match: (-match.strength, _PREFERENCE[match.ecosystem]),
        )
        if not matches:
            raise InvalidInputError(
                f"Couldn't find '{raw.strip()}' in any supported registry. Check the spelling or pick the ecosystem."
            )
        best, *others = matches
        return EcosystemDetection(ecosystem=best.ecosystem, also_found_in=[match.ecosystem for match in others])

    async def _probe(self, adapter: EcosystemAdapter, raw: str) -> _Match | None:
        """None when the registry doesn't publish the name (or couldn't be reached)."""
        name = _name(adapter, raw)
        try:
            if not await adapter.exists(name):
                return None
        except UpstreamError as exc:
            logger.info("Skipping %s during detection: %s", adapter.id, exc)
            return None
        try:
            measure = adoption_measure(await adapter.get_adoption(name), self._policy)
        except UpstreamError:  # it exists; unknown adoption just ranks it last
            measure = None
        return _Match(adapter.id, measure.strength if measure else 0.0)


def _name(adapter: EcosystemAdapter, raw: str) -> str:
    name, _ = adapter.split_spec(raw)
    return adapter.normalize_name(name)


def _fits(adapter: EcosystemAdapter, raw: str) -> bool:
    return adapter.is_valid_name(_name(adapter, raw))
