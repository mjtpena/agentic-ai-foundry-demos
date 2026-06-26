"""FastAPI entry point for the Foundry Live Demo Console.

Generic dispatch: every demo module under ui/server/demos exposes a
`run(stream, payload)` (and optionally `setup(...)`, `status()`), wired to
POST /api/demos/<id>/<action> as an SSE stream. SDK imports live *inside* those
functions so a missing preview package degrades one demo, not the whole server.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .catalog import CATALOG, BY_ID
from .foundry import environment_summary, load_env
from .sse import sse_stream
from .demos import (
    prompt_agent,
    mcp_tools,
    openapi_tool,
    agent_framework,
    guardrails,
    agentic_retrieval,
    a2a_agent,
    hosted_agent,
)

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

DEMO_MODULES = {
    "prompt-agent": prompt_agent,
    "mcp-tools": mcp_tools,
    "openapi-tool": openapi_tool,
    "agent-framework": agent_framework,
    "guardrails": guardrails,
    "agentic-retrieval": agentic_retrieval,
    "a2a-agent": a2a_agent,
    "hosted-agent": hosted_agent,
}

app = FastAPI(title="Foundry Live Demo Console", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    load_env()


@app.get("/api/demos")
def list_demos() -> JSONResponse:
    return JSONResponse(CATALOG)


@app.get("/api/environment")
def get_environment(refresh: bool = False) -> JSONResponse:
    return JSONResponse(environment_summary(refresh=refresh))


@app.get("/api/demos/{demo_id}/status")
def demo_status(demo_id: str) -> JSONResponse:
    module = DEMO_MODULES.get(demo_id)
    if module is None:
        return JSONResponse({"error": "unknown demo"}, status_code=404)
    if hasattr(module, "status"):
        return JSONResponse(module.status())
    return JSONResponse({"status": BY_ID.get(demo_id, {}).get("status", "ready")})


@app.post("/api/demos/{demo_id}/{action}")
async def run_demo(demo_id: str, action: str, request: Request):
    module = DEMO_MODULES.get(demo_id)
    if module is None:
        return JSONResponse({"error": f"unknown demo '{demo_id}'"}, status_code=404)
    handler = getattr(module, action, None)
    if handler is None or not callable(handler):
        return JSONResponse(
            {"error": f"demo '{demo_id}' has no action '{action}'"}, status_code=404
        )
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    return sse_stream(lambda stream: handler(stream, payload))


# Static SPA last, so /api/* routes win.
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
