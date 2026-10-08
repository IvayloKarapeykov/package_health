"""MCP tools for agents. Served over HTTP at /mcp by the API, or over stdio by `python -m app.mcp_server`."""

from collections.abc import Callable
from typing import Annotated

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from pydantic import Field, ValidationError

from app.agent.runner import AnalysisRunner
from app.domain.credentials import Credentials
from app.domain.errors import InvalidInputError
from app.domain.models import AnalysisReport
from app.domain.requests import AUTO_DETECT, EcosystemChoice, ManifestRequest, PackageRequest

INSTRUCTIONS = (
    "Checks whether open source packages are safe to depend on: adoption, maintenance and known "
    "vulnerabilities, with a verdict (recommended, caution or avoid), the reasons and alternatives. "
    "Use check_package before adding a dependency and check_dependencies to review a whole project."
)

# Only reads public registries, GitHub and OSV.dev.
READ_ONLY = ToolAnnotations(read_only_hint=True, idempotent_hint=True, open_world_hint=True)


def build_mcp_server(runners: Callable[[Credentials], AnalysisRunner]) -> MCPServer:
    server = MCPServer("package-health", title="Package Health", instructions=INSTRUCTIONS)

    async def analyze(ctx: Context, request: Callable[[], PackageRequest | ManifestRequest]) -> AnalysisReport:
        # Over HTTP the caller's keys arrive as headers; over stdio there are none and `.env` applies.
        credentials = Credentials.from_headers(ctx.headers or {})
        try:
            return await runners(credentials).run(request())
        except (InvalidInputError, ValidationError) as exc:
            raise ToolError(str(exc)) from exc

    @server.tool(annotations=READ_ONLY)
    async def check_package(
        package: Annotated[
            str,
            Field(description="Package name, optionally with a version: express, requests>=2.31, org.slf4j:slf4j-api"),
        ],
        ctx: Context,
        ecosystem: Annotated[
            EcosystemChoice, Field(description="Registry to look in; auto picks the one where the name is most used")
        ] = AUTO_DETECT,
    ) -> AnalysisReport:
        """Check one package: verdict, health score, reasons, vulnerabilities and alternatives."""
        return await analyze(ctx, lambda: PackageRequest(package=package, ecosystem=ecosystem))

    @server.tool(annotations=READ_ONLY)
    async def check_dependencies(
        content: Annotated[
            str,
            Field(description="Full text of a dependency file: package.json, requirements.txt, pom.xml, go.mod, ..."),
        ],
        ctx: Context,
        filename: Annotated[str | None, Field(description="File name, if known; otherwise detected")] = None,
        include_dev: Annotated[bool, Field(description="Also check development dependencies")] = True,
    ) -> AnalysisReport:
        """Check every dependency in a file, worst first. Takes longer: up to 8 packages run at once."""
        return await analyze(ctx, lambda: ManifestRequest(content=content, filename=filename, include_dev=include_dev))

    return server
