"""Packagist (PHP / Composer): package metadata, abandonment status and downloads in one call."""

import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.cache import TTLCache
from app.core.http import JsonHttpClient
from app.core.time import parse_iso_datetime
from app.domain.models import Adoption, RegistryInfo
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.releases import release_stats, weekly_from

API_URL = "https://packagist.org/packages"
# Tagged, stable releases only: "1.2.3" / "v1.2.3" (not "dev-main", "2.x-dev", "3.0.0-RC1").
_STABLE_VERSION = re.compile(r"^v?\d+(?:\.\d+)*$")


@dataclass(frozen=True)
class _Package:
    info: RegistryInfo
    adoption: Adoption


class PackagistAdapter(EcosystemAdapter):
    id = "packagist"
    osv_ecosystem = "Packagist"
    # https://getcomposer.org/doc/04-schema.md#name
    name_pattern = re.compile(r"^[a-z0-9]([_.-]?[a-z0-9]+)*/[a-z0-9](([_.]|-{1,2})?[a-z0-9]+)*$")

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache) -> None:
        self._json = JsonHttpClient(http, source="registry")
        self._cache = cache

    def normalize_name(self, raw: str) -> str:
        return raw.strip().lower()

    def split_spec(self, raw: str) -> tuple[str, str | None]:
        # Composer uses "vendor/package:^1.2" on the command line; accept "@" too.
        spec = raw.strip()
        for separator in (":", "@"):
            if separator in spec:
                name, _, version = spec.partition(separator)
                return name, version or None
        return spec, None

    def package_url(self, name: str) -> str:
        return f"https://packagist.org/packages/{name}"

    async def get_package(self, name: str) -> RegistryInfo:
        return (await self._package(name)).info

    async def get_adoption(self, name: str) -> Adoption:
        return (await self._package(name)).adoption

    async def _package(self, name: str) -> _Package:
        return await self._cache.get_or_load(f"packagist:{name}", lambda: self._fetch(name))

    async def _fetch(self, name: str) -> _Package:
        document = await self._json.get(f"{API_URL}/{name}.json")
        package = document["package"]
        downloads = package.get("downloads") or {}
        monthly = downloads.get("monthly")
        return _Package(
            info=parse_packagist_package(package, registry_url=self.package_url(name)),
            adoption=Adoption(
                weekly_downloads=weekly_from(monthly, 30) if monthly is not None else None,
                total_downloads=downloads.get("total"),
                note="weekly average over the last 30 days",
            ),
        )


def parse_packagist_package(package: dict[str, Any], *, registry_url: str) -> RegistryInfo:
    # Stable versions with a release date: version -> (record, released_at).
    releases = {
        version: (record, released_at)
        for version, record in (package.get("versions") or {}).items()
        if _STABLE_VERSION.match(version) and (released_at := parse_iso_datetime(record.get("time")))
    }
    latest = max(releases, key=lambda v: releases[v][1], default=None)
    if latest is None:
        latest = next(iter(package.get("versions") or {}), "dev")
    record = releases[latest][0] if latest in releases else {}
    stats = release_stats(released_at for _, released_at in releases.values())

    abandoned = package.get("abandoned")
    deprecated = None
    if isinstance(abandoned, str) and abandoned:
        deprecated = f"Abandoned; the maintainers suggest {abandoned} instead"
    elif abandoned:
        deprecated = "Abandoned by its maintainers"

    return RegistryInfo(
        latest_version=latest.removeprefix("v"),
        registry_url=registry_url,
        description=package.get("description") or None,
        license=" OR ".join(record.get("license") or []) or None,
        homepage=record.get("homepage"),
        repository_url=package.get("repository"),
        created_at=parse_iso_datetime(package.get("time")) or stats.created_at,
        last_release_at=stats.last_release_at,
        total_versions=stats.total_versions,
        releases_last_year=stats.releases_last_year,
        deprecated=deprecated,
        dependencies_count=len([d for d in record.get("require") or {} if "/" in d]),
    )
