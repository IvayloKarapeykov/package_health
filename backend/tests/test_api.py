from collections.abc import Iterator
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.credentials import Credentials
from app.main import create_app


@pytest.fixture
def client(make_runner) -> Iterator[TestClient]:
    app = create_app()
    with TestClient(app) as test_client:
        runner, _ = make_runner()  # swap real upstreams for fakes
        app.state.runners = lambda _credentials: runner
        yield test_client


def test_analyze_returns_camel_case_report(client: TestClient) -> None:
    response = client.post("/api/analyze", json={"mode": "package", "ecosystem": "npm", "package": "healthy-lib"})
    assert response.status_code == 200
    body = response.json()
    assert body["overallVerdict"] == "recommended"
    assert body["assessments"][0]["signals"]["adoption"]["weeklyDownloads"] == 2_500_000


def test_analyze_rejects_invalid_package_names(client: TestClient) -> None:
    response = client.post("/api/analyze", json={"mode": "package", "ecosystem": "maven", "package": "guava"})
    assert response.status_code == 422


def test_analyze_stream_emits_server_sent_events(client: TestClient) -> None:
    payload = {"mode": "manifest", "content": "module example.com/app\n\nrequire github.com/pkg/errors v0.9.1\n"}
    with client.stream("POST", "/api/analyze/stream", json=payload) as response:
        body = "".join(response.iter_text())
    assert [line for line in body.splitlines() if line.startswith("event:") and "progress" not in line] == [
        "event: plan",
        "event: assessment",
        "event: report",
    ]


def test_ecosystems_lists_every_ecosystem_with_its_manifests(client: TestClient) -> None:
    ecosystems = {item["id"]: item["manifests"] for item in client.get("/api/ecosystems").json()}
    assert len(ecosystems) == 8
    assert ecosystems["pypi"] == ["pyproject.toml", "Pipfile", "requirements.txt"]
    assert ecosystems["maven"] == ["pom.xml", "build.gradle"]


def test_keys_in_headers_reach_the_runner_factory(client: TestClient) -> None:
    app = cast(FastAPI, client.app)
    keyless_runner = app.state.runners(Credentials())
    received: list[Credentials] = []
    app.state.runners = lambda credentials: received.append(credentials) or keyless_runner

    payload = {"mode": "package", "ecosystem": "npm", "package": "healthy-lib"}
    client.post("/api/analyze", json=payload, headers={"X-GitHub-Token": "gh-123", "X-OpenRouter-Key": "  "})
    client.post("/api/analyze", json=payload)

    with_keys, without_keys = received
    assert with_keys.github_token is not None and with_keys.github_token.get_secret_value() == "gh-123"
    assert with_keys.openrouter_api_key is None  # blank counts as absent
    assert without_keys.empty
