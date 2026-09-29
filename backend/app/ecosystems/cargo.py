"""crates.io (Rust): one crates.io API call carries metadata, versions and recent downloads."""

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

API_URL = "https://crates.io/api/v1/crates"
RECENT_DOWNLOADS_DAYS = 90  # crates.io's "recent_downloads" window


@dataclass(frozen=True)
class _Crate:
    info: RegistryInfo
    adoption: Adoption


class CargoAdapter(EcosystemAdapter):
    id = "cargo"
    osv_ecosystem = "crates.io"
    bare_version_is_exact = False  # in Cargo.toml "1.2.3" means "^1.2.3"
    name_pattern = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache) -> None:
        self._json = JsonHttpClient(http, source="registry")
        self._cache = cache

    def normalize_name(self, raw: str) -> str:
        return raw.strip().lower()

    def package_url(self, name: str) -> str:
        return f"https://crates.io/crates/{name}"

    async def get_package(self, name: str) -> RegistryInfo:
        return (await self._crate(name)).info

    async def get_adoption(self, name: str) -> Adoption:
        return (await self._crate(name)).adoption

    async def _crate(self, name: str) -> _Crate:
        return await self._cache.get_or_load(f"cargo:{name}", lambda: self._fetch(name))

    async def _fetch(self, name: str) -> _Crate:
        document = await self._json.get(f"{API_URL}/{name}")
        return _Crate(
            info=parse_crate_document(document, registry_url=self.package_url(name)),
            adoption=_adoption(document["crate"]),
        )


def parse_crate_document(document: dict[str, Any], *, registry_url: str) -> RegistryInfo:
    crate = document["crate"]
    versions: list[dict[str, Any]] = document.get("versions") or []
    latest = crate.get("default_version") or crate.get("max_stable_version") or crate.get("newest_version")
    latest_record = next((v for v in versions if v.get("num") == latest), {})
    live = [v for v in versions if not v.get("yanked")]
    stats = release_stats(d for v in live if (d := parse_iso_datetime(v.get("created_at"))))
    deprecated = "Every published version has been yanked" if versions and not live else None

    return RegistryInfo(
        latest_version=latest,
        registry_url=registry_url,
        description=crate.get("description"),
        license=latest_record.get("license"),
        homepage=crate.get("homepage"),
        repository_url=crate.get("repository"),
        created_at=parse_iso_datetime(crate.get("created_at")) or stats.created_at,
        last_release_at=stats.last_release_at,
        total_versions=stats.total_versions,
        releases_last_year=stats.releases_last_year,
        deprecated=deprecated,
    )


def _adoption(crate: dict[str, Any]) -> Adoption:
    recent = crate.get("recent_downloads")
    return Adoption(
        weekly_downloads=weekly_from(recent, RECENT_DOWNLOADS_DAYS) if recent is not None else None,
        total_downloads=crate.get("downloads"),
        note="weekly average over the last 90 days",
    )
