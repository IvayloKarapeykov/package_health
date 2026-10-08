"""Composition root: wires settings, clients, services and the graph together.

Keys come per request (see `Credentials`), with the server's `.env` keys as the fallback. Everything that
doesn't need a key — HTTP client, cache, registries, OSV — is built once and shared by every request.
"""

from dataclasses import dataclass

import httpx
from pydantic import SecretStr

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
from app.domain.credentials import Credentials
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


def build_decider(settings: Settings, http: httpx.AsyncClient, api_key: SecretStr | None) -> VerdictDecider:
    rules = RuleVerdictDecider()
    if api_key is None or not settings.use_jev_verdicts:
        return rules
    jev = JevClient(
        http,
        api_key=api_key.get_secret_value(),
        model=settings.jev_model,
        url=settings.openrouter_decisions_url,
    )
    return JevVerdictDecider(jev, fallback=rules)


def build_explainer(settings: Settings, api_key: SecretStr | None) -> Explainer:
    heuristic = HeuristicExplainer()
    model = build_chat_model(settings, api_key)
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


@dataclass(frozen=True)
class Upstreams:
    """The clients that need no key. Shared, so one cache serves every caller (it holds public data only)."""

    http: httpx.AsyncClient
    cache: TTLCache
    ecosystems: EcosystemRegistry
    osv: OsvClient


def build_upstreams(settings: Settings, http: httpx.AsyncClient) -> Upstreams:
    cache = TTLCache(ttl_seconds=settings.cache_ttl_seconds)
    return Upstreams(http=http, cache=cache, ecosystems=build_ecosystems(http, cache), osv=OsvClient(http, cache))


def build_services(settings: Settings, upstreams: Upstreams, credentials: Credentials) -> AgentServices:
    keys = credentials.or_defaults(settings.github_token, settings.openrouter_api_key)
    github_token = keys.github_token.get_secret_value() if keys.github_token else None
    http, ecosystems = upstreams.http, upstreams.ecosystems

    return AgentServices(
        input_parser=DependencyInputParser(ecosystems, max_packages=settings.max_packages),
        detector=EcosystemDetector(ecosystems),
        collector=SignalCollector(ecosystems, GitHubClient(http, upstreams.cache, github_token), upstreams.osv),
        scorer=HealthScorer(),
        decider=build_decider(settings, http, keys.openrouter_api_key),
        explainer=build_explainer(settings, keys.openrouter_api_key),
        alternatives=AlternativeVerifier(ecosystems),
    )


class RunnerFactory:
    """The analysis runner for a request's credentials. Requests without keys share one runner built at
    startup; a request with keys gets its own, so keys never outlive the request or leak between callers."""

    def __init__(self, settings: Settings, http: httpx.AsyncClient) -> None:
        self._settings = settings
        self._upstreams = build_upstreams(settings, http)
        self._keyless = self._build(Credentials())

    def __call__(self, credentials: Credentials) -> AnalysisRunner:
        return self._keyless if credentials.empty else self._build(credentials)

    def _build(self, credentials: Credentials) -> AnalysisRunner:
        graph = build_graph(build_services(self._settings, self._upstreams, credentials))
        return AnalysisRunner(graph, max_concurrency=self._settings.max_concurrency)
