"""pnpm, Yarn and Bun install from the npm registry too, so they share this adapter."""

import re
from typing import Any

import httpx

from app.core.cache import TTLCache
from app.core.http import JsonHttpClient, NotFoundError
from app.core.time import parse_iso_datetime
from app.domain.models import Adoption, RegistryInfo
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.releases import release_stats

REGISTRY_URL = "https://registry.npmjs.org"
DOWNLOADS_URL = "https://api.npmjs.org/downloads/point/last-week"

_TIME_META_KEYS = {"created", "modified", "unpublished"}


class NpmAdapter(EcosystemAdapter):
    id = "npm"
    osv_ecosystem = "npm"
    # https://github.com/npm/validate-npm-package-name (lower-case, url-safe, optional scope)
    name_pattern = re.compile(r"^(?:@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*$")

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache) -> None:
        self._registry = JsonHttpClient(http, source="registry")
        self._downloads = JsonHttpClient(http, source="adoption")
        self._cache = cache

    def normalize_name(self, raw: str) -> str:
        return raw.strip().lower()

    def package_url(self, name: str) -> str:
        return f"https://www.npmjs.com/package/{name}"

    async def get_package(self, name: str) -> RegistryInfo:
        return await self._cache.get_or_load(f"npm:package:{name}", lambda: self._fetch_package(name))

    async def get_adoption(self, name: str) -> Adoption:
        return await self._cache.get_or_load(f"npm:downloads:{name}", lambda: self._fetch_downloads(name))

    async def exists(self, name: str) -> bool:
        # The downloads API 404s for unknown packages and is far lighter than a full packument.
        try:
            await self.get_adoption(name)
        except NotFoundError:
            return False
        return True

    async def _fetch_package(self, name: str) -> RegistryInfo:
        # Scoped names must keep their "@" but have the "/" encoded: @scope%2Fname
        document = await self._registry.get(f"{REGISTRY_URL}/{name.replace('/', '%2F')}")
        return parse_registry_document(document, registry_url=self.package_url(name))

    async def _fetch_downloads(self, name: str) -> Adoption:
        payload = await self._downloads.get(f"{DOWNLOADS_URL}/{name}")
        return Adoption(weekly_downloads=int(payload.get("downloads", 0)), note="last 7 days")


def parse_registry_document(document: dict[str, Any], *, registry_url: str) -> RegistryInfo:
    """Extract the health-relevant facts from a full npm packument."""
    latest = (document.get("dist-tags") or {}).get("latest")
    versions: dict[str, Any] = document.get("versions") or {}
    if not latest or latest not in versions:
        raise NotFoundError("registry", "package has no published versions (unpublished?)")

    manifest = versions[latest]
    times: dict[str, Any] = document.get("time") or {}
    stats = release_stats(
        parsed
        for version, raw in times.items()
        if version not in _TIME_META_KEYS
        and version in versions
        and (parsed := parse_iso_datetime(raw)) is not None
    )

    return RegistryInfo(
        latest_version=latest,
        registry_url=registry_url,
        description=manifest.get("description") or document.get("description"),
        license=_license_name(manifest.get("license") or document.get("license")),
        homepage=manifest.get("homepage") or document.get("homepage"),
        repository_url=_repository_url(manifest.get("repository") or document.get("repository")),
        created_at=parse_iso_datetime(times.get("created")) or stats.created_at,
        last_release_at=stats.last_release_at,
        total_versions=len(versions),
        releases_last_year=stats.releases_last_year,
        deprecated=_deprecation_message(manifest.get("deprecated")),
        maintainers_count=len(document.get("maintainers") or []),
        dependencies_count=len(manifest.get("dependencies") or {}),
        unpacked_size_bytes=(manifest.get("dist") or {}).get("unpackedSize"),
        has_types=bool(manifest.get("types") or manifest.get("typings"))
        or str(document.get("name", "")).startswith("@types/"),
    )


def _license_name(raw: Any) -> str | None:
    if isinstance(raw, dict):
        return raw.get("type")
    return raw if isinstance(raw, str) else None


def _repository_url(raw: Any) -> str | None:
    if isinstance(raw, dict):
        return raw.get("url")
    return raw if isinstance(raw, str) else None


def _deprecation_message(raw: Any) -> str | None:
    # npm stores `deprecated` as a message string; `true` also appears in the wild.
    if raw is True:
        return "This version is deprecated."
    return raw if isinstance(raw, str) and raw.strip() else None
