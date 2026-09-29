"""Date helpers shared across clients and scoring."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def days_since(moment: datetime | None, now: datetime) -> int | None:
    if moment is None:
        return None
    return max((now - moment).days, 0)
