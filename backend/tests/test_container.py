"""Per-request keys: which decider and explainer a request gets, and which runner serves it."""

import httpx
from pydantic import SecretStr

from app.agent.jev_decider import JevVerdictDecider
from app.agent.llm_explainer import LlmExplainer
from app.container import RunnerFactory, build_services, build_upstreams
from app.core.config import Settings
from app.domain.credentials import Credentials
from app.services.advice import HeuristicExplainer, RuleVerdictDecider


def settings(**keys: str) -> Settings:
    """Settings that ignore `.env` and the environment's keys."""
    return Settings(_env_file=None, **{"openrouter_api_key": None, "github_token": None, **keys})  # type: ignore[call-arg]


async def test_without_any_key_verdicts_and_explanations_are_rule_based() -> None:
    async with httpx.AsyncClient() as http:
        services = build_services(settings(), build_upstreams(settings(), http), Credentials())
    assert isinstance(services.decider, RuleVerdictDecider)
    assert isinstance(services.explainer, HeuristicExplainer)


async def test_a_request_key_enables_jev_and_the_llm() -> None:
    async with httpx.AsyncClient() as http:
        credentials = Credentials.from_raw(openrouter_api_key="sk-or-request")
        services = build_services(settings(), build_upstreams(settings(), http), credentials)
    assert isinstance(services.decider, JevVerdictDecider)
    assert isinstance(services.explainer, LlmExplainer)


async def test_the_server_key_is_the_fallback() -> None:
    server = settings(openrouter_api_key="sk-or-server")
    async with httpx.AsyncClient() as http:
        services = build_services(server, build_upstreams(server, http), Credentials())
    assert isinstance(services.decider, JevVerdictDecider)


def test_request_keys_win_over_server_keys() -> None:
    keys = Credentials.from_raw(github_token="request").or_defaults(SecretStr("server"), SecretStr("server-or"))
    assert keys.github_token is not None and keys.github_token.get_secret_value() == "request"
    assert keys.openrouter_api_key is not None and keys.openrouter_api_key.get_secret_value() == "server-or"


async def test_keyless_requests_share_a_runner_and_keyed_requests_get_their_own() -> None:
    async with httpx.AsyncClient() as http:
        runners = RunnerFactory(settings(), http)
        keyed = Credentials.from_raw(github_token="gh")
        assert runners(Credentials()) is runners(Credentials.from_raw("", " "))
        assert runners(keyed) is not runners(keyed)
        assert runners(keyed) is not runners(Credentials())
