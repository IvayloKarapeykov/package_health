from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request
from sse_starlette import EventSourceResponse, ServerSentEvent
from starlette.background import BackgroundTask

from app.agent.runner import AnalysisRunner
from app.api.limits import AnalysisLease, LimitExceeded, client_ip
from app.core.config import Settings, get_settings
from app.domain.credentials import GITHUB_TOKEN_HEADER, OPENROUTER_KEY_HEADER, Credentials
from app.domain.ecosystems import ECOSYSTEMS
from app.domain.errors import InvalidInputError
from app.domain.models import AnalysisReport
from app.domain.requests import AnalysisRequest
from app.manifests.registry import MANIFEST_PARSERS

router = APIRouter(prefix="/api")

# Keep-alive comments let clients detect a dead connection (the frontend times out after 15s of silence).
SSE_PING_SECONDS = 5


# Callers' own keys, used for that request only. Missing ones fall back to the server's .env keys.
def get_credentials(
    github_token: Annotated[
        str | None, Header(alias=GITHUB_TOKEN_HEADER, description="GitHub token: 5,000 requests/hour instead of 60")
    ] = None,
    openrouter_key: Annotated[
        str | None, Header(alias=OPENROUTER_KEY_HEADER, description="OpenRouter key: AI verdicts and explanations")
    ] = None,
) -> Credentials:
    return Credentials.from_raw(github_token, openrouter_key)


def get_runner(request: Request, credentials: Annotated[Credentials, Depends(get_credentials)]) -> AnalysisRunner:
    return request.app.state.runners(credentials)


def admit(request: Request) -> AnalysisLease:
    client = client_ip(request.headers, request.client.host if request.client else None)
    try:
        return request.app.state.limits.acquire(client)
    except LimitExceeded as exc:
        raise HTTPException(status_code=429, detail=exc.message, headers={"Retry-After": str(exc.retry_after)}) from exc


Runner = Annotated[AnalysisRunner, Depends(get_runner)]
RequestBody = Annotated[AnalysisRequest, Body()]


@router.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
    """The server's own keys, used when a request brings none."""
    return {
        "status": "ok",
        "llm": settings.llm_model if settings.openrouter_api_key else None,
        "verdictModel": settings.jev_model if settings.openrouter_api_key and settings.use_jev_verdicts else None,
        "githubAuthenticated": settings.github_token is not None,
        "tracing": settings.langsmith_project if settings.langsmith_tracing and settings.langsmith_api_key else None,
    }


@router.get("/ecosystems")
async def ecosystems() -> list[dict[str, object]]:
    """Supported ecosystems and the dependency files each one understands."""
    return [
        {
            "id": ecosystem,
            "label": info.label,
            "language": info.language,
            "manifests": [p.format for p in MANIFEST_PARSERS if p.ecosystem == ecosystem],
        }
        for ecosystem, info in ECOSYSTEMS.items()
    ]


@router.post("/analyze", response_model=AnalysisReport)
async def analyze(body: RequestBody, runner: Runner, request: Request) -> AnalysisReport:
    with admit(request):
        try:
            return await runner.run(body)
        except InvalidInputError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyze/stream")
async def analyze_stream(body: RequestBody, runner: Runner, request: Request) -> EventSourceResponse:
    lease = admit(request)

    async def events() -> AsyncIterator[ServerSentEvent]:
        try:
            async for event in runner.stream(body):
                yield ServerSentEvent(event=event.type, data=event.model_dump_json())
        finally:
            lease.release()

    # The background task covers a stream that never starts; release() only counts once.
    return EventSourceResponse(events(), ping=SSE_PING_SECONDS, background=BackgroundTask(lease.release))
