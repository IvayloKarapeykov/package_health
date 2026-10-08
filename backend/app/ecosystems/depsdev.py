"""deps.dev API (https://docs.deps.dev/api/v3/): versions, deprecation, licenses and links."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from app.core.cache import TTLCache
from app.core.http import JsonHttpClient, NotFoundError, UpstreamError
from app.core.time import parse_iso_datetime
from app.domain.models import Adoption, RegistryInfo
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.releases import release_stats

API_URL = "https://api.deps.dev"
# Go pseudo-versions (untagged commits) are not releases: v0.0.0-20190101000000-abcdef123456
_PSEUDO_VERSION = re.compile(r"\d{14}-[0-9a-f]{12}$")


@dataclass(frozen=True)
class DepsDevPackage:
    default_version: str
    release_dates: list[datetime]
    version: dict[str, Any]  # the default version's full record


class DepsDevClient:
    def __init__(self, http: httpx.AsyncClient, cache: TTLCache) -> None:
        self._json = JsonHttpClient(http, source="deps.dev")
        self._cache = cache

    async def package(self, system: str, name: str) -> DepsDevPackage:
        return await self._cache.get_or_load(f"depsdev:{system}:{name}", lambda: self._fetch(system, name))

    async def dependents(self, system: str, name: str, version: str) -> int | None:
        url = f"{API_URL}/v3alpha/systems/{system}/packages/{quote(name, safe='')}/versions/{quote(version, safe='')}:dependents"
        try:
            payload = await self._json.get(url)
        except NotFoundError:
            return None  # deps.dev hasn't computed dependents for this package
        return payload.get("dependentCount")

    async def _fetch(self, system: str, name: str) -> DepsDevPackage:
        base = f"{API_URL}/v3/systems/{system}/packages/{quote(name, safe='')}"
        package = await self._json.get(base)
        versions = package.get("versions") or []
        default = next((v for v in versions if v.get("isDefault")), None)
        if default is None:
            raise NotFoundError("deps.dev", "package has no default version")
        version = default["versionKey"]["version"]
        record = await self._json.get(f"{base}/versions/{quote(version, safe='')}")
        dates = [
            parsed
            for v in versions
            if not _PSEUDO_VERSION.search(v["versionKey"]["version"])
            and (parsed := parse_iso_datetime(v.get("publishedAt"))) is not None
        ]
        return DepsDevPackage(default_version=version, release_dates=dates, version=record)


def source_repository(record: dict[str, Any]) -> str | None:
    for link in record.get("links") or []:
        if link.get("label") == "SOURCE_REPO":
            return link.get("url")
    for project in record.get("relatedProjects") or []:
        if project.get("relationType") == "SOURCE_REPO":
            return f"https://{project['projectKey']['id']}"
    return None


def homepage(record: dict[str, Any]) -> str | None:
    return next((link["url"] for link in record.get("links") or [] if link.get("label") == "HOMEPAGE"), None)


class DepsDevAdapter(EcosystemAdapter):
    """An ecosystem whose metadata comes from deps.dev; subclasses add description and adoption."""

    system: str  # deps.dev's system name, e.g. "GO"

    def __init__(self, depsdev: DepsDevClient, http: httpx.AsyncClient, cache: TTLCache) -> None:
        self._depsdev = depsdev
        self._extras = JsonHttpClient(http, source=self.id)
        self._cache = cache

    async def get_package(self, name: str) -> RegistryInfo:
        package = await self._depsdev.package(self.system, name)
        record = package.version
        stats = release_stats(package.release_dates)
        deprecated = (record.get("deprecatedReason") or "This version is deprecated.") if record.get("isDeprecated") else None
        return RegistryInfo(
            latest_version=package.default_version,
            registry_url=self.package_url(name),
            description=await self.description(name),
            license=" AND ".join(record.get("licenses") or []) or None,
            homepage=homepage(record),
            repository_url=source_repository(record),
            created_at=stats.created_at,
            last_release_at=stats.last_release_at,
            total_versions=stats.total_versions,
            releases_last_year=stats.releases_last_year,
            deprecated=deprecated,
        )

    async def description(self, name: str) -> str | None:
        """Hook: deps.dev has no package descriptions; subclasses may fetch one."""
        return None

    async def get_adoption(self, name: str) -> Adoption:
        return Adoption()

    async def _extra(self, url: str, **params: Any) -> Any | None:
        """GET a best-effort, cached JSON extra (description, downloads); failures mean less data."""
        key = f"{self.id}:extra:{url}:{sorted(params.items())}"
        try:
            return await self._cache.get_or_load(key, lambda: self._extras.get(url, params=params or None))
        except UpstreamError:
            return None
