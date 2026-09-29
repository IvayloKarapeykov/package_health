import json

import httpx
import pytest
import respx

from app.agent.jev_decider import JevVerdictDecider
from app.agent.prompts import VERDICT_CRITERIA
from app.clients.jev import DECISIONS_URL, JevClient
from app.core.http import UpstreamError
from app.domain.models import Verdict
from app.services.advice import RuleVerdictDecider
from app.services.scoring import HealthScorer
from tests.factories import healthy_signals


def jev_response(choice: str, confidence: float = 0.9) -> httpx.Response:
    probabilities = {option: (confidence if option == choice else 0.0) for option in VERDICT_CRITERIA}
    return httpx.Response(
        200,
        json={
            "model": "typesafe/jev-1.13-20260917",
            "answers": {"answer": {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": probabilities}},
            "usage": {"input_tokens": 400, "output_tokens": 40, "cost": 0.00002},
        },
    )


async def decide(signals, health=None):
    async with httpx.AsyncClient() as http:
        decider = JevVerdictDecider(JevClient(http, api_key="test", model="typesafe/jev-1.13"), RuleVerdictDecider())
        return await decider.decide(signals, health or HealthScorer().score(signals))


@respx.mock
async def test_jev_choice_becomes_the_verdict_with_its_confidence() -> None:
    route = respx.post(DECISIONS_URL).mock(return_value=jev_response("caution", 0.82))
    decision = await decide(healthy_signals())

    assert (decision.verdict, decision.confidence, decision.source) == (Verdict.CAUTION, 0.82, "jev")
    body = json.loads(route.calls.last.request.content)
    assert body["model"] == "typesafe/jev-1.13"
    assert body["questions"]["answer"]["type"] == "choice"
    assert set(body["questions"]["answer"]["criteria"]) == {"recommended", "caution", "avoid"}
    assert route.calls.last.request.headers["authorization"] == "Bearer test"


@respx.mock
async def test_state_uses_plain_language_not_raw_dates() -> None:
    route = respx.post(DECISIONS_URL).mock(return_value=jev_response("recommended"))
    await decide(healthy_signals())

    state = json.loads(route.calls.last.request.content)["state"]
    assert "20 days ago" in state["release_activity"] or "3 weeks ago" in state["release_activity"]
    assert "T" not in state["release_activity"]  # no ISO timestamps
    assert "verdict" not in json.dumps(state).lower()  # Jev decides independently of the rules


@respx.mock
async def test_critical_findings_force_avoid_without_asking_jev() -> None:
    route = respx.post(DECISIONS_URL).mock(return_value=jev_response("recommended"))
    signals = healthy_signals()
    signals.registry.deprecated = "use something else"
    decision = await decide(signals)

    assert (decision.verdict, decision.source) == (Verdict.AVOID, "rules")
    assert not route.called


@pytest.mark.parametrize(
    "response",
    [httpx.Response(503), httpx.Response(200, json={"answers": {}}), jev_response("maybe")],
)
@respx.mock
async def test_falls_back_to_the_rule_verdict_when_jev_fails(response: httpx.Response) -> None:
    respx.post(DECISIONS_URL).mock(return_value=response)
    decision = await decide(healthy_signals())

    assert (decision.verdict, decision.source, decision.confidence) == (Verdict.RECOMMENDED, "rules", None)


@respx.mock
async def test_client_rejects_unknown_options() -> None:
    respx.post(DECISIONS_URL).mock(return_value=jev_response("maybe"))
    async with httpx.AsyncClient() as http:
        with pytest.raises(UpstreamError):
            await JevClient(http, api_key="k", model="m").choose({}, instructions="?", criteria={"a": "x", "b": "y"})
