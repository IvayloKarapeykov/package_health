"""Abuse limits for the public API and MCP endpoint: analyses per client, analyses at once, and body size.

The counters live in memory, so they apply per server process.
"""

import logging
import math
import time
from collections import defaultdict, deque
from collections.abc import Mapping

from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger(__name__)


class LimitExceeded(Exception):
    def __init__(self, message: str, retry_after: int) -> None:
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class AnalysisLease:
    """One running analysis. Releasing it twice is harmless, so every exit path can call release()."""

    def __init__(self, limits: "AnalysisLimits") -> None:
        self._limits = limits
        self._released = False

    def release(self) -> None:
        if not self._released:
            self._released = True
            self._limits.finish()

    def __enter__(self) -> "AnalysisLease":
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


class AnalysisLimits:
    def __init__(self, max_per_client: int, window_seconds: float, max_active: int) -> None:
        self._max_per_client = max_per_client
        self._window = window_seconds
        self._max_active = max_active
        self._active = 0
        self._starts: defaultdict[str, deque[float]] = defaultdict(deque)

    def acquire(self, client: str) -> AnalysisLease:
        """Admit one analysis for `client`, or raise LimitExceeded. Release the lease when it ends."""
        if self._active >= self._max_active:
            logger.info("Analysis refused: server busy")
            raise LimitExceeded("Too many analyses are running right now. Try again in a minute.", retry_after=30)

        now = time.monotonic()
        starts = self._starts[client]
        while starts and starts[0] <= now - self._window:
            starts.popleft()
        if len(starts) >= self._max_per_client:
            retry_after = math.ceil(starts[0] + self._window - now)
            logger.info("Analysis refused: client over its limit")
            raise LimitExceeded(
                f"You've reached the limit of {self._max_per_client} analyses per "
                f"{round(self._window / 60)} minutes. Try again in {retry_after} seconds.",
                retry_after=retry_after,
            )

        starts.append(now)
        self._active += 1
        self._forget_idle_clients(now)
        return AnalysisLease(self)

    def finish(self) -> None:
        self._active -= 1

    def _forget_idle_clients(self, now: float) -> None:
        if len(self._starts) < 10_000:
            return
        for client in [c for c, starts in self._starts.items() if not starts or starts[-1] <= now - self._window]:
            del self._starts[client]


def client_ip(headers: Mapping[str, str], peer: str | None) -> str:
    """The last X-Forwarded-For entry is the one our proxy added; earlier ones come from the client and can be faked."""
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    return peer or "unknown"


class BodySizeLimitMiddleware:
    """Rejects request bodies over `max_bytes` with 413, by Content-Length or while reading a chunked body."""

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and (not declared.isdigit() or int(declared) > self._max_bytes):
            await self._reject(send)
            return

        received = 0
        started = False
        rejected = False

        # FastAPI turns any error raised while reading the body into a 400, so the 413 is sent from here
        # and the app is told the client went away; whatever it sends afterwards is dropped.
        async def limited_receive() -> Message:
            nonlocal received, rejected
            message = await receive()
            if message["type"] == "http.request" and not rejected:
                received += len(message.get("body", b""))
                if received > self._max_bytes:
                    rejected = True
                    if not started:
                        await self._reject(send)
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal started
            if rejected:
                return
            started = started or message["type"] == "http.response.start"
            await send(message)

        await self._app(scope, limited_receive, guarded_send)

    async def _reject(self, send: Send) -> None:
        body = b'{"detail":"The request body is too large."}'
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})
