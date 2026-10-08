"""Drops suggested alternatives that don't exist in the package's registry (LLMs invent names)."""

import asyncio
from typing import Protocol

from app.core.http import UpstreamError
from app.domain.models import Alternative, DependencyRef
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.registry import EcosystemRegistry
from app.services.advice import AlternativeSuggestion

MAX_ALTERNATIVES = 3


class AlternativeChecker(Protocol):
    async def verify(self, dependency: DependencyRef, suggestions: list[AlternativeSuggestion]) -> list[Alternative]: ...


class AlternativeVerifier:
    def __init__(self, ecosystems: EcosystemRegistry) -> None:
        self._ecosystems = ecosystems

    async def verify(self, dependency: DependencyRef, suggestions: list[AlternativeSuggestion]) -> list[Alternative]:
        adapter = self._ecosystems.get(dependency.ecosystem)
        candidates = _unique_candidates(adapter, dependency.name, suggestions)[:MAX_ALTERNATIVES]
        verified = await asyncio.gather(*(self._verify_one(adapter, candidate) for candidate in candidates))
        return [alternative for alternative in verified if alternative is not None]

    @staticmethod
    async def _verify_one(adapter: EcosystemAdapter, suggestion: AlternativeSuggestion) -> Alternative | None:
        try:
            if not await adapter.exists(suggestion.name):
                return None  # hallucinated, mistyped, or from another ecosystem
        except UpstreamError:
            pass  # registry hiccup: keep the suggestion rather than silently dropping it
        try:
            adoption = await adapter.get_adoption(suggestion.name)
        except UpstreamError:
            adoption = None
        return Alternative(
            name=suggestion.name,
            reason=suggestion.reason,
            url=adapter.package_url(suggestion.name),
            adoption=adoption,
        )


def _unique_candidates(
    adapter: EcosystemAdapter, package_name: str, suggestions: list[AlternativeSuggestion]
) -> list[AlternativeSuggestion]:
    seen = {package_name}
    unique: list[AlternativeSuggestion] = []
    for suggestion in suggestions:
        name = adapter.normalize_name(suggestion.name)
        if name in seen or not adapter.is_valid_name(name):
            continue
        seen.add(name)
        unique.append(suggestion.model_copy(update={"name": name}))
    return unique
