"""OpenRouter's API is OpenAI-compatible, so ChatOpenAI works with a different base URL."""

from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings

APP_TITLE = "Package Health Advisor"


def build_chat_model(settings: Settings, api_key: SecretStr | None) -> ChatOpenAI | None:
    if api_key is None:
        return None
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=api_key,
        base_url=settings.openrouter_base_url,
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
        max_retries=2,
        default_headers={"X-Title": APP_TITLE},
    )
