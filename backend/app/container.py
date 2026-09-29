"""Composition root: wires settings, clients, services and the graph together."""

import httpx

from app.agent.graph import build_graph
from app.agent.jev_decider import JevVerdictDecider
from app.agent.llm import build_chat_model
from app.agent.llm_explainer import LlmExplainer
from app.agent.runner import AnalysisRunner
from app.agent.services import AgentServices
from app.clients.github import GitHubClient
from app.clients.jev import JevClient
from app.clients.osv import OsvClient
from app.core.cache import TTLCache
from app.core.config import Settings
from app.ecosystems.cargo import CargoAdapter
from app.ecosystems.depsdev import DepsDevClient
from app.ecosystems.depsdev_ecosystems import GoAdapter, MavenAdapter, NuGetAdapter, RubyGemsAdapter
from app.ecosystems.npm import NpmAdapter
from app.ecosystems.packagist import PackagistAdapter
from app.ecosystems.pypi import PyPIAdapter
from app.ecosystems.registry import EcosystemRegistry
from app.services.advice import Explainer, HeuristicExplainer, RuleVerdictDecider, VerdictDecider
from app.services.alternatives import AlternativeVerifier
from app.services.ecosystem_detection import EcosystemDetector
from app.services.package_input import DependencyInputParser
from app.services.scoring import HealthScorer
from app.services.signals import SignalCollector


def build_decider(settings: Settings, http: httpx.AsyncClient) -> VerdictDecider:
    rules = RuleVerdictDecider()
    if settings.openrouter_api_key is None or not settings.use_jev_verdicts:
        return rules
    jev = JevClient(
        http,
        api_key=settings.openrouter_api_key.get_secret_value(),
        model=settings.jev_model,
        url=settings.openrouter_decisions_url,
    )
    return JevVerdictDecider(jev, fallback=rules)


def build_explainer(settings: Settings) -> Explainer:
    heuristic = HeuristicExplainer()
    model = build_chat_model(settings)
    if model is None:
        return heuristic
    return LlmExplainer(model, fallback=heuristic, structured_output_method=settings.llm_structured_output_method)


def build_ecosystems(http: httpx.AsyncClient, cache: TTLCache) -> EcosystemRegistry:
    depsdev = DepsDevClient(http, cache)
    return EcosystemRegistry(
        [
            NpmAdapter(http, cache),
            PyPIAdapter(http, cache, depsdev),
            CargoAdapter(http, cache),
            PackagistAdapter(http, cache),
            GoAdapter(depsdev, http, cache),
            MavenAdapter(depsdev, http, cache),
            NuGetAdapter(depsdev, http, cache),
            RubyGemsAdapter(depsdev, http, cache),
        ]
    )


def build_services(settings: Settings, http: httpx.AsyncClient) -> AgentServices:
    cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)
    github_token = settings.github_token.get_secret_value() if settings.github_token else None
    ecosystems = build_ecosystems(http, cache)

    return AgentServices(
        input_parser=DependencyInputParser(ecosystems, max_packages=settings.max_packages),
        detector=EcosystemDetector(ecosystems),
        collector=SignalCollector(ecosystems, GitHubClient(http, cache, github_token), OsvClient(http, cache)),
        scorer=HealthScorer(),
        decider=build_decider(settings, http),
        explainer=build_explainer(settings),
        alternatives=AlternativeVerifier(ecosystems),
    )


def build_runner(settings: Settings, http: httpx.AsyncClient) -> AnalysisRunner:
    graph = build_graph(build_services(settings, http))
    return AnalysisRunner(graph, max_concurrency=settings.max_concurrency)
