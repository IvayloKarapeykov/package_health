import json
import logging
from typing import Literal

import pytest
from fastapi.testclient import TestClient

from app.agent.telemetry import run_config, run_summary
from app.core.logs import JsonFormatter, TextFormatter, fields, new_request_id, request_id_var
from app.domain.models import PackageAssessment, SourceIssue, Verdict, VerdictSource
from app.domain.requests import ManifestRequest, PackageRequest
from app.main import create_app
from app.services.scoring import HealthScorer
from tests.factories import healthy_signals


@pytest.fixture
def client(make_runner):
    app = create_app()
    with TestClient(app) as test_client:
        runner, _ = make_runner()
        app.state.runners = lambda _credentials: runner
        yield test_client


def test_every_response_carries_a_request_id(client: TestClient) -> None:
    minted = client.get("/api/health").headers["X-Request-ID"]
    echoed = client.get("/api/health", headers={"X-Request-ID": "proxy-abc.123"}).headers["X-Request-ID"]
    rejected = client.get("/api/health", headers={"X-Request-ID": "bad id\n" * 20}).headers["X-Request-ID"]

    assert len(minted) == 16
    assert echoed == "proxy-abc.123"  # a caller's well-formed ID is kept, so logs line up across services
    assert rejected != "bad id\n" * 20


def test_stream_errors_quote_the_request_id(client: TestClient) -> None:
    response = client.post(
        "/api/analyze/stream",
        json={"mode": "package", "ecosystem": "npm", "package": "Not Valid!"},
        headers={"X-Request-ID": "req-42"},
    )
    error = next(line for line in response.text.splitlines() if line.startswith("data:"))
    assert json.loads(error.removeprefix("data:"))["requestId"] == "req-42"


async def test_graph_logs_carry_the_request_id_and_a_run_summary(make_runner, caplog) -> None:
    runner, _ = make_runner()
    token = request_id_var.set("req-7")
    try:
        with caplog.at_level(logging.INFO, logger="app.agent.runner"):
            events = [event async for event in runner.stream(PackageRequest(package="healthy-lib", ecosystem="npm"))]
    finally:
        request_id_var.reset(token)

    assert events[-1].type == "report"
    finished = next(r for r in caplog.records if r.getMessage().startswith("Analysis finished"))
    summary = finished.fields  # type: ignore[attr-defined]
    assert (summary["packages"], summary["verdict_sources"], summary["explanation_sources"]) == (
        1,
        {"rules": 1},
        {"heuristic": 1},
    )
    record = logging.makeLogRecord({**finished.__dict__})
    record.request_id = "req-7"
    assert json.loads(JsonFormatter().format(record))["request_id"] == "req-7"


def test_formatters_render_structured_fields() -> None:
    record = logging.LogRecord("app.x", logging.INFO, __file__, 1, "Checked %s", ("npm",), None)
    record.__dict__.update(fields(status=200, verdicts={"avoid": 2}))
    record.request_id = "abc"

    entry = json.loads(JsonFormatter().format(record))
    assert (entry["message"], entry["status"], entry["verdicts"], entry["request_id"]) == (
        "Checked npm",
        200,
        {"avoid": 2},
        "abc",
    )
    assert TextFormatter().format(record).endswith("app.x [abc]: Checked npm status=200 verdicts=avoid:2")


def test_run_config_tags_and_links_the_trace_to_the_request() -> None:
    token = request_id_var.set("req-9")
    try:
        package = run_config({"max_concurrency": 8}, PackageRequest(package="serde", ecosystem="auto"))
        manifest = run_config({}, ManifestRequest(content="flask\n", filename="requirements.txt"))
    finally:
        request_id_var.reset(token)

    assert (package["run_name"], package["tags"], package["max_concurrency"]) == (
        "package-health-analysis",
        ["mode:package", "ecosystem:auto"],
        8,
    )
    assert package["metadata"] == {"request_id": "req-9", "package": "serde"}
    assert manifest["metadata"]["content_chars"] == 6  # the file itself isn't copied into metadata


SOURCES: list[tuple[VerdictSource, Literal["llm", "heuristic"]]] = [("jev", "llm"), ("rules", "heuristic")]


def test_run_summary_counts_silent_fallbacks() -> None:
    from app.core.time import utc_now
    from app.domain.models import AnalysisReport

    signals = healthy_signals()
    signals.issues.append(SourceIssue(source="github", message="rate limit reached"))
    health = HealthScorer().score(signals)
    assessments = [
        PackageAssessment(
            dependency=signals.dependency,
            verdict=Verdict.CAUTION,
            score=health.score,
            summary="",
            signals=signals,
            verdict_source=source,
            explanation_source=explanation,
        )
        for source, explanation in SOURCES
    ]
    report = AnalysisReport(
        ecosystem="npm",
        overall_verdict=Verdict.CAUTION,
        summary="",
        counts={verdict: 2 if verdict == Verdict.CAUTION else 0 for verdict in Verdict},
        assessments=assessments,
        generated_at=utc_now(),
    )
    summary = run_summary(report, duration_ms=1200)
    assert summary["verdict_sources"] == {"jev": 1, "rules": 1}
    assert summary["explanation_sources"] == {"llm": 1, "heuristic": 1}
    assert summary["upstream_issues"] == {"github": 2}
    assert summary["verdicts"] == {"caution": 2}


def test_new_request_id_validates_incoming() -> None:
    assert new_request_id("abc-123") == "abc-123"
    assert new_request_id("x" * 65) != "x" * 65
    assert new_request_id(None) != new_request_id(None)


async def test_request_id_reaches_nodes_running_in_parallel_branches(make_runner) -> None:
    from tests.test_graph import FakeCollector

    seen: list[str | None] = []

    class RecordingCollector(FakeCollector):
        async def collect(self, dependency, on_stage=None):
            seen.append(request_id_var.get())  # what every log line inside this node would carry
            return await super().collect(dependency, on_stage)

    runner, _ = make_runner(RecordingCollector())
    token = request_id_var.set("req-fanout")
    try:
        request = ManifestRequest(content="a>=1\nb>=1\nc>=1\n", filename="requirements.txt")
        [event async for event in runner.stream(request)]
    finally:
        request_id_var.reset(token)

    assert seen == ["req-fanout"] * 3
