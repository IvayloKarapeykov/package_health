"""LLM-backed explainer. Falls back to the heuristic explainer whenever the model call fails."""

import logging
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.agent.prompts import (
    EXPLAIN_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    build_explanation_input,
    build_summary_input,
)
from app.domain.models import HealthScore, PackageAssessment, PackageSignals, Verdict
from app.services.advice import AlternativeSuggestion, Explainer, Explanation

logger = logging.getLogger(__name__)

StructuredOutputMethod = Literal["function_calling", "json_schema", "json_mode"]

# Models occasionally answer without calling the structured-output tool; one retry usually fixes it.
MAX_ATTEMPTS = 2


class LlmExplanation(BaseModel):
    """Your explanation of the package's verdict."""

    summary: str = Field(description="One or two plain sentences")
    reasons: list[str] = Field(description="2-5 short, data-backed reasons")
    alternatives: list[AlternativeSuggestion] = Field(
        default_factory=list, description="Up to 3 real packages from the same ecosystem; empty if none are needed"
    )


class LlmExplainer:
    def __init__(
        self,
        model: BaseChatModel,
        fallback: Explainer,
        structured_output_method: StructuredOutputMethod = "function_calling",
    ) -> None:
        self._model = model
        self._structured = model.with_structured_output(LlmExplanation, method=structured_output_method)
        self._fallback = fallback

    async def explain(self, signals: PackageSignals, health: HealthScore, verdict: Verdict) -> Explanation:
        messages = [
            SystemMessage(EXPLAIN_SYSTEM_PROMPT),
            HumanMessage(build_explanation_input(signals, health, verdict)),
        ]
        result = await self._structured_explanation(messages)
        if result is None:
            logger.warning("LLM explanation failed for %s; using heuristic", signals.dependency.key)
            return await self._fallback.explain(signals, health, verdict)

        return Explanation(
            summary=result.summary.strip(),
            reasons=[reason.strip() for reason in result.reasons if reason.strip()],
            alternatives=result.alternatives,
            source="llm",
        )

    async def _structured_explanation(self, messages: list) -> LlmExplanation | None:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                return LlmExplanation.model_validate(await self._structured.ainvoke(messages))
            except Exception:  # any provider/parsing failure should degrade, not break the report
                logger.info("LLM explanation attempt %d/%d failed", attempt, MAX_ATTEMPTS, exc_info=True)
        return None

    async def summarize(self, assessments: list[PackageAssessment]) -> str:
        if len(assessments) == 1:
            return assessments[0].summary
        messages = [
            SystemMessage(SUMMARY_SYSTEM_PROMPT),
            HumanMessage(build_summary_input(assessments)),
        ]
        try:
            response = await self._model.ainvoke(messages)
            summary = response.text.strip()
        except Exception:
            logger.warning("LLM summary failed; using heuristic", exc_info=True)
            summary = ""
        return summary or await self._fallback.summarize(assessments)
