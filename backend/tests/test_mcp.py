import json
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp import Client

from app.domain.credentials import Credentials
from app.main import create_app
from app.mcp_server import build_mcp_server


@pytest.fixture
def server(make_runner):
    runner, _ = make_runner()
    return build_mcp_server(lambda _credentials: runner)


async def test_lists_both_tools_as_read_only(server) -> None:
    async with Client(server) as client:
        tools = {tool.name: tool for tool in (await client.list_tools()).tools}
    assert set(tools) == {"check_package", "check_dependencies"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in tools.values())


async def test_check_package_returns_the_report(server) -> None:
    async with Client(server) as client:
        result = await client.call_tool("check_package", {"package": "healthy-lib", "ecosystem": "npm"})
    assert not result.is_error
    assert result.structured_content is not None
    assert result.structured_content["overallVerdict"] == "recommended"


async def test_check_dependencies_reads_a_file(server) -> None:
    content = "module example.com/app\n\nrequire github.com/pkg/errors v0.9.1\n"
    async with Client(server) as client:
        result = await client.call_tool("check_dependencies", {"content": content})
    assert result.structured_content is not None
    assert result.structured_content["manifest"] == "go.mod"


async def test_invalid_input_is_a_tool_error(server) -> None:
    async with Client(server) as client:
        result = await client.call_tool("check_package", {"package": "guava", "ecosystem": "maven"})
    assert result.is_error


def test_http_endpoint_passes_header_keys_to_the_runner(make_runner) -> None:
    runner, _ = make_runner()
    received: list[Credentials] = []
    app = create_app()
    with TestClient(app, base_url="http://localhost:8000") as client:
        cast(FastAPI, client.app).state.runners = lambda credentials: received.append(credentials) or runner
        response = client.post(
            "/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "X-GitHub-Token": "gh-123",
                "X-OpenRouter-Key": "sk-or-456",
            },
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "check_package", "arguments": {"package": "healthy-lib", "ecosystem": "npm"}},
            },
        )
    assert response.status_code == 200
    data = next(line for line in response.text.splitlines() if line.startswith("data:"))
    assert json.loads(data.removeprefix("data:"))["result"]["structuredContent"]["overallVerdict"] == "recommended"
    [credentials] = received
    assert credentials.github_token is not None and credentials.github_token.get_secret_value() == "gh-123"
    assert (
        credentials.openrouter_api_key is not None and credentials.openrouter_api_key.get_secret_value() == "sk-or-456"
    )


def test_http_endpoint_rejects_unknown_hosts() -> None:
    with TestClient(create_app(), base_url="http://evil.example") as client:
        response = client.post("/mcp", headers={"Accept": "application/json, text/event-stream"}, json={})
    assert response.status_code == 421
