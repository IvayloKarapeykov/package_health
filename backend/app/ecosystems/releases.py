"""Release-history statistics, computed the same way for every ecosystem."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.time import utc_now


@dataclass(frozen=True)
class ReleaseStats:
    created_at: datetime | None
    last_release_at: datetime | None
    total_versions: int
    releases_last_year: int


def release_stats(release_dates: Iterable[datetime]) -> ReleaseStats:
    dates = list(release_dates)
    one_year_ago = utc_now() - timedelta(days=365)
    return ReleaseStats(
        created_at=min(dates, default=None),
        last_release_at=max(dates, default=None),
        total_versions=len(dates),
        releases_last_year=sum(1 for released in dates if released >= one_year_ago),
    )


def weekly_from(downloads: int, window_days: int) -> int:
    """Normalize a download count over `window_days` to a weekly figure."""
    return round(downloads * 7 / window_days)
