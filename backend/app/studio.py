"""Entry point for `langgraph dev` / LangGraph Studio (see langgraph.json).

The FastAPI app builds the graph inside its lifespan; the LangGraph server instead imports a
module-level graph, so this module wires one up with its own long-lived HTTP client.
"""

from app.agent.graph import build_graph
from app.container import build_services
from app.core.config import get_settings
from app.core.http import create_http_client

_settings = get_settings()

graph = build_graph(build_services(_settings, create_http_client(_settings.http_timeout_seconds)))
