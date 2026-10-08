from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.transport_security import TransportSecuritySettings

from app.api.middleware import REQUEST_ID_HEADER, RequestContextMiddleware
from app.api.routes import router
from app.container import RunnerFactory
from app.core.config import get_settings
from app.core.http import create_http_client
from app.core.logs import configure_logging
from app.core.tracing import configure_tracing
from app.mcp_server import build_mcp_server


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    async with create_http_client(settings.http_timeout_seconds) as http, app.state.mcp.session_manager.run():
        app.state.runners = RunnerFactory(settings, http)
        yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level, settings.log_format)
    configure_tracing(settings)  # before any graph runs: LangSmith reads its settings once

    app = FastAPI(title="Package Health Advisor", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=[REQUEST_ID_HEADER],
    )
    # Added last, so it runs first: the request ID is set before anything else (CORS responses included).
    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)

    # Resolves the runner per call, so tools see the one the lifespan builds.
    app.state.mcp = build_mcp_server(lambda credentials: app.state.runners(credentials))
    mcp_app = app.state.mcp.streamable_http_app(
        streamable_http_path="/mcp",
        stateless_http=True,
        transport_security=TransportSecuritySettings(
            allowed_hosts=settings.mcp_allowed_hosts, allowed_origins=settings.cors_origins
        ),
    )
    # Mounted at the root rather than at /mcp, which would redirect /mcp to /mcp/.
    app.mount("/", mcp_app)
    return app


app = create_app()
