def shorten(text: str | None, limit: int) -> str | None:
    """`text` on one line, cut to `limit` characters."""
    if not text:
        return None
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"
