import re
from typing import Any

import httpx

from app.core.cache import TTLCache
from app.core.http import JsonHttpClient, UpstreamError
from app.core.time import parse_iso_datetime
from app.domain.models import Adoption, RegistryInfo
from app.ecosystems.base import EcosystemAdapter
from app.ecosystems.depsdev import DepsDevClient
from app.ecosystems.releases import release_stats

REGISTRY_URL = "https://pypi.org/pypi"
STATS_URL = "https://pypistats.org/api/packages"

_INACTIVE_CLASSIFIER = "Development Status :: 7 - Inactive"
_TYPED_CLASSIFIER = "Typing :: Typed"
_REPO_URL_KEYS = ("source", "source code", "repository", "code", "github", "homepage", "home")
# name, optional [extras], then nothing or a PEP 440 specifier / environment marker.
_SPEC_PATTERN = re.compile(r"^(?P<name>[A-Za-z0-9._-]+)\s*(?:\[[^\]]*\])?\s*(?P<spec>(?:[=<>!~;].*)?)$")


class PyPIAdapter(EcosystemAdapter):
    id = "pypi"
    osv_ecosystem = "PyPI"
    # https://packaging.python.org/en/latest/specifications/name-normalization/
    name_pattern = re.compile(r"^([a-z0-9]|[a-z0-9][a-z0-9._-]*[a-z0-9])$")

    def __init__(self, http: httpx.AsyncClient, cache: TTLCache, depsdev: DepsDevClient) -> None:
        self._registry = JsonHttpClient(http, source="registry")
        self._stats = JsonHttpClient(http, source="adoption")
        self._depsdev = depsdev
        self._cache = cache

    def normalize_name(self, raw: str) -> str:
        return re.sub(r"[-_.]+", "-", raw.strip()).lower()

    def split_spec(self, raw: str) -> tuple[str, str | None]:
        spec = raw.strip()
        if "@" in spec and not any(op in spec for op in "=<>~!"):
            name, _, version = spec.partition("@")  # tolerate npm-style "requests@2.31.0"
            return name, f"=={version}" if version else None
        match = _SPEC_PATTERN.match(spec)
        if not match:
            return spec, None
        return match.group("name"), match.group("spec").strip() or None

    def package_url(self, name: str) -> str:
        return f"https://pypi.org/project/{name}/"

    async def get_package(self, name: str) -> RegistryInfo:
        return await self._cache.get_or_load(f"pypi:package:{name}", lambda: self._fetch_package(name))

    async def get_adoption(self, name: str) -> Adoption:
        return await self._cache.get_or_load(f"pypi:downloads:{name}", lambda: self._fetch_adoption(name))

    async def _fetch_package(self, name: str) -> RegistryInfo:
        document = await self._registry.get(f"{REGISTRY_URL}/{name}/json")
        return parse_pypi_document(document, registry_url=self.package_url(name))

    async def _fetch_adoption(self, name: str) -> Adoption:
        try:
            payload = await self._stats.get(f"{STATS_URL}/{name}/recent")
        except UpstreamError as exc:
            if not exc.rate_limited:
                raise
            # pypistats throttles bursts (a big requirements.txt); fall back to deps.dev's dependents.
            package = await self._depsdev.package("PYPI", name)
            dependents = await self._depsdev.dependents("PYPI", name, package.default_version)
            return Adoption(dependents=dependents, note="dependent packages (download stats were rate limited)")
        return Adoption(weekly_downloads=(payload.get("data") or {}).get("last_week"), note="last 7 days")


def parse_pypi_document(document: dict[str, Any], *, registry_url: str) -> RegistryInfo:
    info = document["info"]
    classifiers: list[str] = info.get("classifiers") or []
    stats = release_stats(
        min(uploaded)
        for files in (document.get("releases") or {}).values()
        if (uploaded := [d for f in files if not f.get("yanked") and (d := parse_iso_datetime(f.get("upload_time_iso_8601")))])
    )
    deprecated = None
    if _INACTIVE_CLASSIFIER in classifiers:
        deprecated = f"Marked inactive by its maintainers ({_INACTIVE_CLASSIFIER})"
    elif info.get("yanked"):
        deprecated = f"The latest release was yanked: {info.get('yanked_reason') or 'no reason given'}"

    return RegistryInfo(
        latest_version=info["version"],
        registry_url=registry_url,
        description=info.get("summary") or None,
        license=_license(info, classifiers),
        homepage=info.get("home_page") or None,
        repository_url=_repository_url(info),
        created_at=stats.created_at,
        last_release_at=stats.last_release_at,
        total_versions=stats.total_versions,
        releases_last_year=stats.releases_last_year,
        deprecated=deprecated,
        dependencies_count=sum(1 for req in info.get("requires_dist") or [] if "extra ==" not in req),
        has_types=_TYPED_CLASSIFIER in classifiers,
    )


def _license(info: dict[str, Any], classifiers: list[str]) -> str | None:
    if expression := info.get("license_expression"):
        return expression
    license_text = (info.get("license") or "").strip()
    if license_text and len(license_text) <= 60 and "\n" not in license_text:
        return license_text
    for classifier in classifiers:
        if classifier.startswith("License :: OSI Approved :: "):
            return classifier.rsplit(" :: ", 1)[-1]
    return None


def _repository_url(info: dict[str, Any]) -> str | None:
    urls = {key.lower(): url for key, url in (info.get("project_urls") or {}).items() if url}
    github_urls = [url for url in urls.values() if "github.com" in url]
    for key in _REPO_URL_KEYS:
        if key in urls and "github.com" in urls[key]:
            return urls[key]
    if github_urls:
        return github_urls[0]
    return next((urls[key] for key in _REPO_URL_KEYS if key in urls), None) or info.get("home_page") or None
