"""Entry point for `langgraph dev` / LangGraph Studio (see langgraph.json).

The FastAPI app builds the graph inside its lifespan; the LangGraph server instead imports a
module-level graph, so this module wires one up with its own long-lived HTTP client.
"""

from app.agent.graph import build_graph
from app.container import build_services, build_upstreams
from app.core.config import get_settings
from app.core.http import create_http_client
from app.domain.credentials import Credentials

_settings = get_settings()

# Studio runs on the `.env` keys.
_upstreams = build_upstreams(_settings, create_http_client(_settings.http_timeout_seconds))
graph = build_graph(build_services(_settings, _upstreams, Credentials()))
