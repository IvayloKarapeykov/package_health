import json

import httpx
import pytest
import respx

from app.clients.github import GitHubClient, parse_github_repository
from app.clients.osv import QUERY_URL, OsvClient
from app.core.cache import TTLCache
from app.core.http import UpstreamError
from app.domain.models import Severity


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("git+https://github.com/lodash/lodash.git", ("lodash", "lodash")),
        ("git://github.com/expressjs/express.git", ("expressjs", "express")),
        ("git@github.com:vercel/next.js.git", ("vercel", "next.js")),
        ("https://github.com/facebook/react/tree/main/packages/react", ("facebook", "react")),
        ("https://github.com/rails/rails/tree/v8.1.4", ("rails", "rails")),
        ("github:sindresorhus/got", ("sindresorhus", "got")),
        ("sindresorhus/ky", ("sindresorhus", "ky")),
        ("https://gitlab.com/owner/repo", None),
        (None, None),
    ],
)
def test_parse_github_repository(url: str | None, expected: tuple[str, str] | None) -> None:
    assert parse_github_repository(url) == expected


@respx.mock
async def test_github_rate_limit_is_reported_clearly() -> None:
    respx.get(url__startswith="https://api.github.com/repos/acme/demo").mock(
        return_value=httpx.Response(403, headers={"x-ratelimit-remaining": "0"})
    )
    async with httpx.AsyncClient() as http:
        client = GitHubClient(http, TTLCache(60))
        with pytest.raises(UpstreamError) as error:
            await client.get_repository("acme", "demo")
    assert error.value.rate_limited
    assert "GITHUB_TOKEN" in error.value.message


@respx.mock
async def test_osv_queries_the_given_ecosystem_and_maps_severity() -> None:
    route = respx.post(QUERY_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "vulns": [
                    {"id": "GHSA-1", "summary": "Prototype pollution", "database_specific": {"severity": "MODERATE"}},
                    {"id": "GHSA-2", "details": "Line one\nLine two"},
                    {"id": "GHSA-3", "withdrawn": "2024-01-01T00:00:00Z"},
                ]
            },
        )
    )
    async with httpx.AsyncClient() as http:
        vulns = await OsvClient(http, TTLCache(60)).query("PyPI", "demo", "1.0.0")

    assert json.loads(route.calls.last.request.content) == {
        "package": {"name": "demo", "ecosystem": "PyPI"},
        "version": "1.0.0",
    }
    assert [(v.id, v.severity, v.summary) for v in vulns] == [
        ("GHSA-1", Severity.MODERATE, "Prototype pollution"),
        ("GHSA-2", Severity.UNKNOWN, "Line one"),
    ]
