"""Chat model factory. OpenRouter exposes an OpenAI-compatible API, so ChatOpenAI works as-is."""

from langchain_openai import ChatOpenAI

from app.core.config import Settings

APP_TITLE = "Package Health Advisor"


def build_chat_model(settings: Settings) -> ChatOpenAI | None:
    """The configured chat model, or None when no OpenRouter key is set."""
    if settings.openrouter_api_key is None:
        return None
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
        max_retries=2,
        default_headers={"X-Title": APP_TITLE},
    )
