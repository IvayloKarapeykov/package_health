"""HTTP routes."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.agent.runner import AnalysisRunner
from app.core.config import Settings, get_settings
from app.domain.ecosystems import ECOSYSTEMS
from app.domain.errors import InvalidInputError
from app.domain.models import AnalysisReport
from app.domain.requests import AnalysisRequest
from app.manifests.registry import MANIFEST_PARSERS

router = APIRouter(prefix="/api")

# Keep-alive comments let clients detect a dead connection (the frontend times out after 15s of silence).
SSE_PING_SECONDS = 5


def get_runner(request: Request) -> AnalysisRunner:
    return request.app.state.runner


Runner = Annotated[AnalysisRunner, Depends(get_runner)]
RequestBody = Annotated[AnalysisRequest, Body()]


@router.get("/health")
async def health(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, object]:
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
async def analyze(body: RequestBody, runner: Runner) -> AnalysisReport:
    try:
        return await runner.run(body)
    except InvalidInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/analyze/stream")
async def analyze_stream(body: RequestBody, runner: Runner) -> EventSourceResponse:
    async def events() -> AsyncIterator[ServerSentEvent]:
        async for event in runner.stream(body):
            yield ServerSentEvent(event=event.type, data=event.model_dump_json())

    return EventSourceResponse(events(), ping=SSE_PING_SECONDS)
