from typing import Any

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from app.agent.llm_explainer import LlmExplainer, LlmExplanation
from app.domain.models import Verdict
from app.services.advice import AlternativeSuggestion, HeuristicExplainer
from app.services.scoring import HealthScorer
from tests.factories import healthy_signals


class StructuredFakeModel(FakeListChatModel):
    """Fake chat model whose structured output is a canned value (or an exception)."""

    structured_result: Any = None

    def with_structured_output(self, schema, **kwargs):
        result = self.structured_result

        def respond(_messages):
            if isinstance(result, Exception):
                raise result
            return result

        return RunnableLambda(respond)


async def test_llm_explanation_is_used_when_the_model_answers() -> None:
    explanation = LlmExplanation(
        summary="Maintenance mode.",
        reasons=["Only bug fixes land now."],
        alternatives=[AlternativeSuggestion(name="dayjs", reason="Smaller")],
    )
    explainer = LlmExplainer(StructuredFakeModel(responses=["ok"], structured_result=explanation), HeuristicExplainer())
    signals = healthy_signals()
    result = await explainer.explain(signals, HealthScorer().score(signals), Verdict.CAUTION)

    assert (result.summary, result.source, result.alternatives[0].name) == ("Maintenance mode.", "llm", "dayjs")


async def test_falls_back_to_heuristic_for_the_same_verdict_when_the_model_fails() -> None:
    model = StructuredFakeModel(responses=["ok"], structured_result=RuntimeError("provider down"))
    explainer = LlmExplainer(model, HeuristicExplainer())
    signals = healthy_signals()
    result = await explainer.explain(signals, HealthScorer().score(signals), Verdict.CAUTION)

    assert result.source == "heuristic"
    assert result.summary.startswith("Usable, but")  # the caution copy, not the rule verdict's
