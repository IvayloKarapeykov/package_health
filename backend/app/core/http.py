"""Shared HTTP plumbing for the upstream API clients (npm, GitHub, OSV)."""

import logging
import time
from typing import Any

import httpx

from app.core.logs import fields

USER_AGENT = "package-health-advisor/1.0"

logger = logging.getLogger("app.upstream")


class UpstreamError(Exception):
    """An upstream API was unreachable or answered with an error status."""

    def __init__(
        self,
        source: str,
        message: str,
        *,
        status_code: int | None = None,
        rate_limited: bool = False,
    ) -> None:
        super().__init__(f"{source}: {message}")
        self.source = source
        self.message = message
        self.status_code = status_code
        self.rate_limited = rate_limited


class NotFoundError(UpstreamError):
    """The requested resource does not exist upstream (HTTP 404)."""


def create_http_client(timeout_seconds: float) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=timeout_seconds,
        follow_redirects=True,
        headers={"User-Agent": USER_AGENT},
    )


class JsonHttpClient:
    """Performs JSON requests against one upstream source and maps failures to `UpstreamError`."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        *,
        source: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        self._http = http
        self._source = source
        self._headers = headers or {}

    async def get(self, url: str, *, params: dict[str, Any] | None = None) -> Any:
        return await self._request("GET", url, params=params)

    async def post(self, url: str, payload: dict[str, Any]) -> Any:
        return await self._request("POST", url, payload=payload)

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        started = time.perf_counter()
        try:
            response = await self._http.request(method, url, params=params, json=payload, headers=self._headers)
        except httpx.HTTPError as exc:
            logger.warning(
                "Upstream unreachable",
                extra=fields(
                    source=self._source, method=method, url=url, error=type(exc).__name__, duration_ms=_ms(started)
                ),
            )
            raise UpstreamError(self._source, f"request failed ({type(exc).__name__})") from exc

        self._log(method, url, response, started)
        if response.status_code == 404:
            raise NotFoundError(self._source, "not found", status_code=404)
        if response.status_code >= 400:
            rate_limited = _is_rate_limited(response)
            raise UpstreamError(
                self._source,
                "rate limit reached, try again shortly" if rate_limited else f"HTTP {response.status_code}",
                status_code=response.status_code,
                rate_limited=rate_limited,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise UpstreamError(self._source, "invalid JSON response") from exc

    def _log(self, method: str, url: str, response: httpx.Response, started: float) -> None:
        status = response.status_code
        details = fields(source=self._source, method=method, url=url, status=status, duration_ms=_ms(started))
        # GitHub's quota is the scarce one (60/hour without a token); surface it as it runs low.
        if (remaining := response.headers.get("x-ratelimit-remaining")) is not None:
            details["fields"]["ratelimit_remaining"] = int(remaining) if remaining.isdigit() else remaining
        if _is_rate_limited(response):
            logger.warning("Upstream rate limited", extra=details)
        elif status >= 500:
            logger.warning("Upstream server error", extra=details)
        else:
            logger.debug("Upstream call", extra=details)


def _ms(started: float) -> int:
    return round((time.perf_counter() - started) * 1000)


def _is_rate_limited(response: httpx.Response) -> bool:
    if response.status_code == 429:
        return True
    return response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0"
