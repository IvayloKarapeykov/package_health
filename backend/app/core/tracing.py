"""LangSmith tracing, switched on from settings.

LangGraph, LangChain and `@traceable` all read LangSmith's standard environment variables, so
enabling tracing means exporting our settings (which may come from `.env`) under those names
once, at startup, before the first run.
"""

import logging
import os

from app.core.config import Settings

logger = logging.getLogger(__name__)


def configure_tracing(settings: Settings) -> bool:
    """Returns whether tracing is on."""
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
