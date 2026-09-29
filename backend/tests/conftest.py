"""Shared fixtures."""

import httpx
import pytest

from app.agent.graph import build_graph
from app.agent.runner import AnalysisRunner
from app.agent.services import AgentServices
from app.container import build_ecosystems
from app.core.cache import TTLCache
from app.services.advice import HeuristicExplainer, RuleVerdictDecider
from app.services.ecosystem_detection import EcosystemDetector, EcosystemResolver
from app.services.package_input import DependencyInputParser
from app.services.scoring import HealthScorer
from tests.test_graph import FakeAlternatives, FakeCollector


@pytest.fixture
async def make_runner():
    """Builds a runner over the real graph with fake data sources (no network)."""
    async with httpx.AsyncClient() as http:
        ecosystems = build_ecosystems(http, TTLCache(60))

        def factory(
            collector: FakeCollector | None = None,
            max_concurrency: int = 8,
            detector: EcosystemResolver | None = None,
        ):
            collector = collector or FakeCollector()
            services = AgentServices(
                input_parser=DependencyInputParser(ecosystems, max_packages=40),
                detector=detector or EcosystemDetector(ecosystems),
                collector=collector,
                scorer=HealthScorer(),
                decider=RuleVerdictDecider(),
                explainer=HeuristicExplainer(),
                alternatives=FakeAlternatives(),
            )
            return AnalysisRunner(build_graph(services), max_concurrency=max_concurrency), collector

        yield factory
