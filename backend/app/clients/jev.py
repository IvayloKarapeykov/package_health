"""Client for Jev (TypeSafe) via OpenRouter's Decisions API.

Jev is a decision model: given application state and a typed question it returns a typed
answer with calibrated probabilities, never free text. See
https://openrouter.ai/docs/guides/community/jev
"""

from typing import Any

import httpx
from langsmith import traceable
from pydantic import BaseModel, ValidationError

from app.core.http import JsonHttpClient, UpstreamError

DECISIONS_URL = "https://openrouter.ai/api/alpha/decisions"
_QUESTION_KEY = "answer"


class ChoiceAnswer(BaseModel):
    choice: str
    confidence: float
    probabilities: dict[str, float]


class JevClient:
    def __init__(self, http: httpx.AsyncClient, api_key: str, model: str, url: str = DECISIONS_URL) -> None:
        self._json = JsonHttpClient(http, source="jev", headers={"Authorization": f"Bearer {api_key}"})
        self._model = model
        self._url = url

    # Jev is called over plain HTTP, so it is traced explicitly; it nests under the "decide" node.
    @traceable(
        name="jev",
        run_type="llm",
        process_inputs=lambda inputs: {k: inputs[k] for k in ("state", "instructions", "criteria")},
    )
    async def choose(self, state: dict[str, Any], *, instructions: str, criteria: dict[str, str]) -> ChoiceAnswer:
        """Ask a single `choice` question: which of `criteria`'s keys best fits `state`."""
        payload = {
            "model": self._model,
            "state": state,
            "questions": {_QUESTION_KEY: {"type": "choice", "instructions": instructions, "criteria": criteria}},
        }
        response = await self._json.post(self._url, payload)
        try:
            answer = ChoiceAnswer.model_validate(response["answers"][_QUESTION_KEY])
        except (KeyError, TypeError, ValidationError) as exc:
            raise UpstreamError("jev", "unexpected response shape") from exc
        if answer.choice not in criteria:
            raise UpstreamError("jev", f"answered with an unknown option '{answer.choice}'")
        return answer
