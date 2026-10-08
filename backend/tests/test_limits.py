import json
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import limits as limits_module
from app.api.limits import AnalysisLimits, LimitExceeded, client_ip
from app.main import create_app

PACKAGE = {"mode": "package", "ecosystem": "npm", "package": "healthy-lib"}


def test_a_client_is_refused_past_its_limit_until_the_window_passes(monkeypatch) -> None:
    now = [1000.0]
    monkeypatch.setattr(limits_module.time, "monotonic", lambda: now[0])
    limits = AnalysisLimits(max_per_client=2, window_seconds=60, max_active=10)

    limits.acquire("a").release()
    limits.acquire("a").release()
    with pytest.raises(LimitExceeded) as refused:
        limits.acquire("a")
    assert refused.value.retry_after == 60
    limits.acquire("b").release()  # other clients are unaffected

    now[0] += 61
    limits.acquire("a").release()


def test_the_server_refuses_new_analyses_while_full() -> None:
    limits = AnalysisLimits(max_per_client=10, window_seconds=60, max_active=1)
    lease = limits.acquire("a")
    with pytest.raises(LimitExceeded, match="Too many analyses"):
        limits.acquire("b")
    lease.release()
    lease.release()  # a second release must not free a slot that isn't held
    limits.acquire("b")
    with pytest.raises(LimitExceeded):
        limits.acquire("c")


def test_client_ip_trusts_only_the_proxys_forwarded_entry() -> None:
    assert client_ip({"x-forwarded-for": "6.6.6.6, 203.0.113.7"}, "10.0.0.1") == "203.0.113.7"
    assert client_ip({}, "10.0.0.1") == "10.0.0.1"


@pytest.fixture
def client(make_runner):
    app = create_app()
    with TestClient(app, base_url="http://localhost:8000") as test_client:
        runner, _ = make_runner()
        app.state.runners = lambda _credentials: runner
        yield test_client


def set_limits(client: TestClient, **kwargs) -> None:
    cast(FastAPI, client.app).state.limits = AnalysisLimits(**{"window_seconds": 600, **kwargs})


def test_api_answers_429_with_retry_after_past_the_limit(client: TestClient) -> None:
    set_limits(client, max_per_client=1, max_active=5)
    assert client.post("/api/analyze", json=PACKAGE).status_code == 200
    refused = client.post("/api/analyze", json=PACKAGE)
    assert refused.status_code == 429
    assert int(refused.headers["Retry-After"]) > 0
    assert "limit of 1 analyses" in refused.json()["detail"]


def test_a_finished_stream_frees_its_slot(client: TestClient) -> None:
    set_limits(client, max_per_client=10, max_active=1)
    for _ in range(2):
        with client.stream("POST", "/api/analyze/stream", json=PACKAGE) as response:
            assert response.status_code == 200
            assert "event: report" in "".join(response.iter_text())


def test_oversized_bodies_are_rejected_before_parsing(client: TestClient) -> None:
    huge = {"mode": "manifest", "content": "x" * 2_100_000}
    assert client.post("/api/analyze", json=huge).status_code == 413
    chunks = iter([b'{"mode": "manifest", "content": "', b"x" * 2_100_000, b'"}'])
    chunked = client.post("/api/analyze", content=chunks, headers={"Content-Type": "application/json"})
    assert chunked.status_code == 413


def test_mcp_tool_calls_share_the_limit(client: TestClient) -> None:
    set_limits(client, max_per_client=1, max_active=5)
    call = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "check_package", "arguments": {"package": "healthy-lib", "ecosystem": "npm"}},
    }
    headers = {"Accept": "application/json, text/event-stream"}
    results = []
    for _ in range(2):
        response = client.post("/mcp", headers=headers, json=call)
        data = next(line for line in response.text.splitlines() if line.startswith("data:"))
        results.append(json.loads(data.removeprefix("data:"))["result"])
    assert not results[0].get("isError")
    assert results[1]["isError"]
    assert "limit of 1 analyses" in results[1]["content"][0]["text"]
