"""LangGraph, LangChain and `@traceable` read LangSmith's environment variables, so tracing is
enabled by exporting our settings under those names once, before the first run."""

import logging
import os

from app.core.config import Settings

logger = logging.getLogger(__name__)


def configure_tracing(settings: Settings) -> bool:
    if not settings.langsmith_tracing:
        return False
    if settings.langsmith_api_key is None:
        logger.warning("LANGSMITH_TRACING is on but LANGSMITH_API_KEY is missing; tracing stays off")
        return False

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    if settings.langsmith_endpoint:
        os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    if settings.langsmith_hide_inputs:
        os.environ["LANGSMITH_HIDE_INPUTS"] = "true"
    logger.info("LangSmith tracing enabled for project '%s'", settings.langsmith_project)
    return True
