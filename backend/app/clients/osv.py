from typing import Any

import httpx

from app.core.cache import TTLCache
from app.core.http import JsonHttpClient
from app.domain.models import Severity, Vulnerability

QUERY_URL = "https://api.osv.dev/v1/query"

_SEVERITY_ALIASES = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MODERATE": Severity.MODERATE,
    "MEDIUM": Severity.MODERATE,
    "LOW": Severity.LOW,
}


class OsvClient:
    def __init__(self, http: httpx.AsyncClient, cache: TTLCache) -> None:
        self._json = JsonHttpClient(http, source="osv")
        self._cache = cache

    async def query(self, ecosystem: str, name: str, version: str | None = None) -> list[Vulnerability]:
        """Vulnerabilities for a package in an OSV ecosystem ("npm", "PyPI", "Go", ...);
        restricted to one version when `version` is given."""
        return await self._cache.get_or_load(
            f"osv:{ecosystem}:{name}@{version or '*'}", lambda: self._fetch(ecosystem, name, version)
        )

    async def _fetch(self, ecosystem: str, name: str, version: str | None) -> list[Vulnerability]:
        payload: dict[str, Any] = {"package": {"name": name, "ecosystem": ecosystem}}
        if version:
            payload["version"] = version
        response = await self._json.post(QUERY_URL, payload)
        return [
            _to_vulnerability(raw)
            for raw in response.get("vulns") or []
            if not raw.get("withdrawn")
        ]


def _to_vulnerability(raw: dict[str, Any]) -> Vulnerability:
    return Vulnerability(
        id=raw["id"],
        summary=raw.get("summary") or _first_line(raw.get("details")),
        severity=_severity(raw),
        aliases=raw.get("aliases") or [],
        url=f"https://osv.dev/vulnerability/{raw['id']}",
    )


def _severity(raw: dict[str, Any]) -> Severity:
    candidates = [(raw.get("database_specific") or {}).get("severity")]
    candidates += [
        (affected.get("ecosystem_specific") or {}).get("severity")
        for affected in raw.get("affected") or []
    ]
    for label in candidates:
        if isinstance(label, str) and label.upper() in _SEVERITY_ALIASES:
            return _SEVERITY_ALIASES[label.upper()]
    return Severity.UNKNOWN


def _first_line(text: str | None) -> str | None:
    if not text:
        return None
    return text.strip().splitlines()[0][:200]
