"""Client for the GitHub REST API (works unauthenticated at 60 requests/hour)."""

import asyncio
import re

import httpx

from app.core.cache import TTLCache
from app.core.http import JsonHttpClient, UpstreamError
from app.core.time import parse_iso_datetime
from app.domain.models import RepositoryInfo

API_URL = "https://api.github.com"

_GITHUB_REPO_PATTERN = re.compile(
    r"(?:github\.com[/:]|^github:)(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?(?:[/#?].*)?$"
)
_SHORTHAND_PATTERN = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)$")


def parse_github_repository(url: str | None) -> tuple[str, str] | None:
    """Return (owner, repo) for any of the repository URL shapes found in package.json."""
    if not url:
        return None
    url = url.strip()
    match = _GITHUB_REPO_PATTERN.search(url) or _SHORTHAND_PATTERN.match(url)
    if not match:
        return None
    return match.group("owner"), match.group("repo")


class GitHubClient:
    def __init__(self, http: httpx.AsyncClient, cache: TTLCache, token: str | None = None) -> None:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._json = JsonHttpClient(http, source="github", headers=headers)
        self._cache = cache

    async def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        return await self._cache.get_or_load(
            f"github:repo:{owner}/{repo}".lower(), lambda: self._fetch_repository(owner, repo)
        )

    async def _fetch_repository(self, owner: str, repo: str) -> RepositoryInfo:
        base = f"{API_URL}/repos/{owner}/{repo}"
        try:
            details, commits = await asyncio.gather(
                self._json.get(base),
                self._latest_commits(base),
            )
        except UpstreamError as exc:
            if exc.rate_limited:
                raise UpstreamError(
                    "github",
                    "rate limit reached (60 requests/hour without a token; send X-GitHub-Token or set GITHUB_TOKEN)",
                    status_code=exc.status_code,
                    rate_limited=True,
                ) from exc
            raise

        last_commit = commits[0]["commit"]["committer"]["date"] if commits else None
        return RepositoryInfo(
            full_name=details["full_name"],
            url=details["html_url"],
            description=details.get("description"),
            stars=details.get("stargazers_count", 0),
            forks=details.get("forks_count", 0),
            open_issues=details.get("open_issues_count", 0),
            archived=bool(details.get("archived")),
            last_commit_at=parse_iso_datetime(last_commit) or parse_iso_datetime(details.get("pushed_at")),
        )

    async def _latest_commits(self, base: str) -> list[dict]:
        try:
            return await self._json.get(f"{base}/commits", params={"per_page": 1})
        except UpstreamError as exc:
            if exc.status_code == 409:  # empty repository
                return []
            raise
