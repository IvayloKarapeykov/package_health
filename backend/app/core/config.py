from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Empty values, like the blank keys in .env.example, mean "not set" rather than an empty key.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    # LLM (OpenRouter, OpenAI-compatible API)
    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "z-ai/glm-5.3-flash"
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 60.0
    llm_structured_output_method: Literal["function_calling", "json_schema", "json_mode"] = "function_calling"

    # Verdicts from Jev (TypeSafe's decision model) via OpenRouter's Decisions API
    use_jev_verdicts: bool = True
    jev_model: str = "typesafe/jev-1.13"
    openrouter_decisions_url: str = "https://openrouter.ai/api/alpha/decisions"

    # Upstream data sources
    github_token: SecretStr | None = None
    http_timeout_seconds: float = 20.0
    cache_ttl_seconds: int = 900

    # Agent limits
    max_packages: int = 40
    max_concurrency: int = 8

    # Abuse limits for the API and the MCP endpoint
    rate_limit_analyses: int = 30  # per client, per window
    rate_limit_window_seconds: int = 600
    max_active_analyses: int = 6  # across all clients; more get a "busy" answer
    max_request_bytes: int = 2_000_000

    # HTTP server
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Host headers the MCP endpoint answers to (DNS rebinding protection). Add the public domain when deployed.
    mcp_allowed_hosts: list[str] = ["localhost:*", "127.0.0.1:*", "[::1]:*"]

    # Observability
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"  # json for log aggregators in production
    # LangSmith tracing of every graph run (nodes, subgraphs, LLM and Jev calls). Off by default.
    langsmith_tracing: bool = False
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "package-health-advisor"
    langsmith_endpoint: str | None = None  # e.g. the EU region or a self-hosted instance
    # Don't send inputs (pasted dependency files, package facts) to LangSmith; outputs still are.
    langsmith_hide_inputs: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
