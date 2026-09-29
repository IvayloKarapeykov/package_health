"""Verdicts from Jev, a fast decision model; falls back to the rule-based verdict on failure."""

import logging

from app.agent.prompts import VERDICT_CRITERIA, VERDICT_INSTRUCTIONS, build_verdict_state
from app.clients.jev import JevClient
from app.core.http import UpstreamError
from app.domain.models import HealthScore, PackageSignals, Verdict
from app.services.advice import VerdictDecider, VerdictDecision

logger = logging.getLogger(__name__)


class JevVerdictDecider:
    def __init__(self, client: JevClient, fallback: VerdictDecider) -> None:
        self._client = client
        self._fallback = fallback

    async def decide(self, signals: PackageSignals, health: HealthScore) -> VerdictDecision:
        # Hard rules (deprecated, archived, critical vulnerability) are not up for a vote.
        if any(finding.impact == "critical" for finding in health.findings):
            return VerdictDecision(verdict=Verdict.AVOID, source="rules")

        try:
            answer = await self._client.choose(
                build_verdict_state(signals, health),
                instructions=VERDICT_INSTRUCTIONS,
                criteria=VERDICT_CRITERIA,
            )
        except UpstreamError:
            logger.warning("Jev verdict failed for %s; using rules", signals.dependency.name, exc_info=True)
            return await self._fallback.decide(signals, health)

        return VerdictDecision(verdict=Verdict(answer.choice), confidence=answer.confidence, source="jev")
