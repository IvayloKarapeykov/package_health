import asyncio
import sys

from app.container import RunnerFactory
from app.core.config import get_settings
from app.core.http import create_http_client
from app.core.logs import configure_logging
from app.core.tracing import configure_tracing
from app.mcp_server import build_mcp_server


async def main() -> None:
    settings = get_settings()
    # stdout carries the MCP protocol, so logs go to stderr.
    configure_logging(settings.log_level, settings.log_format, stream=sys.stderr)
    configure_tracing(settings)
    async with create_http_client(settings.http_timeout_seconds) as http:
        await build_mcp_server(RunnerFactory(settings, http)).run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())
