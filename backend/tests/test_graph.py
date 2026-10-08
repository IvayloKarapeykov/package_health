import asyncio

import pytest

from app.domain.models import Alternative, DependencyRef, EcosystemDetection, PackageSignals, Verdict
from app.domain.requests import ManifestRequest, PackageRequest
from app.services.advice import AlternativeSuggestion
from tests.factories import healthy_signals


class FakeCollector:
    def __init__(self, delays: dict[str, float] | None = None) -> None:
        self.delays = delays or {}
        self.in_flight = 0
        self.max_in_flight = 0

    async def collect(self, dependency: DependencyRef, on_stage=None) -> PackageSignals:
        if on_stage:
            on_stage("registry")
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            await asyncio.sleep(self.delays.get(dependency.name, 0.01))
            if dependency.name == "explodes":
                raise RuntimeError("boom")
            if dependency.name == "missing":
                return PackageSignals(dependency=dependency)
            signals = healthy_signals(dependency.name, dependency.ecosystem)
            if dependency.name == "request":  # deprecated, with well-known npm alternatives
                signals.registry.deprecated = "no longer maintained"
            return signals.model_copy(update={"dependency": dependency})
        finally:
            self.in_flight -= 1


class FakeAlternatives:
    async def verify(self, dependency: DependencyRef, suggestions: list[AlternativeSuggestion]) -> list[Alternative]:
        return [Alternative(name=s.name, reason=s.reason) for s in suggestions]


def requirements(*names: str) -> ManifestRequest:
    return ManifestRequest(content="\n".join(f"{name}>=1.0" for name in names), filename="requirements.txt")


async def test_single_package_report(make_runner) -> None:
    runner, _ = make_runner()
    report = await runner.run(PackageRequest(package="healthy-lib", ecosystem="npm"))
    assert report.overall_verdict == Verdict.RECOMMENDED
    assert (report.ecosystem, report.manifest) == ("npm", None)
    assert report.summary == report.assessments[0].summary


async def test_fan_out_runs_branches_in_parallel_and_merges_results(make_runner) -> None:
    runner, collector = make_runner()
    report = await runner.run(requirements("a", "b", "request", "missing", "c"))

    assert collector.max_in_flight == 5
    assert (report.ecosystem, report.manifest) == ("pypi", "requirements.txt")
    # Worst verdicts first, then the order from the manifest.
    assert [a.dependency.name for a in report.assessments] == ["request", "a", "b", "c", "missing"]
    assert report.overall_verdict == Verdict.AVOID
    assert (report.counts[Verdict.RECOMMENDED], report.counts[Verdict.UNKNOWN]) == (3, 1)


async def test_max_concurrency_bounds_parallel_branches(make_runner) -> None:
    runner, collector = make_runner(max_concurrency=2)
    await runner.run(requirements("a", "b", "c", "d"))
    assert collector.max_in_flight == 2


async def test_a_crashing_branch_does_not_sink_the_report(make_runner) -> None:
    runner, _ = make_runner()
    report = await runner.run(requirements("a", "explodes"))
    verdicts = {a.dependency.name: a.verdict for a in report.assessments}
    assert verdicts == {"a": Verdict.RECOMMENDED, "explodes": Verdict.UNKNOWN}
    failed = next(a for a in report.assessments if a.dependency.name == "explodes")
    assert "Unexpected error" in failed.signals.issues[-1].message


async def test_subgraph_skips_straight_to_finalize_for_unknown_packages(make_runner) -> None:
    runner, _ = make_runner()
    events = [event async for event in runner.stream(PackageRequest(package="missing", ecosystem="npm"))]
    steps = [event.step for event in events if event.type == "progress"]
    assert steps == ["registry"]  # no scoring, verdict or explanation for a package that doesn't exist
    assert events[-1].report.assessments[0].verdict == Verdict.UNKNOWN


async def test_alternatives_are_verified_only_when_suggested(make_runner) -> None:
    runner, _ = make_runner()
    events = [event async for event in runner.stream(PackageRequest(package="request", ecosystem="npm"))]
    steps = [event.step for event in events if event.type == "progress"]

    assert steps == ["registry", "scoring", "deciding", "explaining", "alternatives"]
    assert [a.name for a in events[-1].report.assessments[0].alternatives] == ["undici", "got", "axios"]


async def test_stream_emits_plan_progress_assessments_then_report(make_runner) -> None:
    runner, _ = make_runner(FakeCollector(delays={"slow": 0.2, "fast": 0.01}))
    events = [event async for event in runner.stream(requirements("slow", "fast"))]
    milestones = [event for event in events if event.type != "progress"]

    assert [event.type for event in milestones] == ["plan", "assessment", "assessment", "report"]
    assert (milestones[0].ecosystem, milestones[0].manifest) == ("pypi", "requirements.txt")
    assert [event.assessment.dependency.name for event in milestones[1:3]] == ["fast", "slow"]
    assert {event.dependency_key for event in events if event.type == "progress"} == {"pypi:slow", "pypi:fast"}


@pytest.mark.parametrize(
    "request_",
    [
        PackageRequest(package="Not Valid!", ecosystem="npm"),
        ManifestRequest(content="{oops", filename="package.json"),
        ManifestRequest(content="just some prose"),
    ],
)
async def test_stream_reports_invalid_input_as_an_error_event(make_runner, request_) -> None:
    runner, _ = make_runner()
    events = [event async for event in runner.stream(request_)]
    assert [(event.type, event.kind) for event in events] == [("error", "invalid_input")]


async def test_graph_accepts_raw_json_requests_like_langgraph_studio_sends(make_runner) -> None:
    runner, _ = make_runner()
    state = await runner._graph.ainvoke({"request": {"mode": "package", "ecosystem": "cargo", "package": "serde"}})
    assert state["report"].assessments[0].dependency.key == "cargo:serde"


async def test_auto_ecosystem_resolves_before_fan_out(make_runner) -> None:
    class FakeDetector:
        async def detect(self, raw: str) -> EcosystemDetection:
            return EcosystemDetection(ecosystem="cargo", also_found_in=["npm"])

    runner, _ = make_runner(detector=FakeDetector())
    events = [event async for event in runner.stream(PackageRequest(package="serde@1"))]
    plan = events[0]

    assert (plan.type, plan.ecosystem, plan.detection.also_found_in) == ("plan", "cargo", ["npm"])
    assert events[-1].report.assessments[0].dependency.key == "cargo:serde"
