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
from .foundry import environment_summary, load_env, current_config, update_config
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
from .codeview import get_code

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


def _demo_payload(demo: dict) -> dict:
    payload = dict(demo)
    module = DEMO_MODULES.get(demo["id"])
    if module is None or not hasattr(module, "status"):
        return payload
    try:
        status = module.status()
    except Exception:
        return payload
    if isinstance(status, dict) and status.get("ready"):
        payload["status"] = "ready"
    return payload


@app.on_event("startup")
def _startup() -> None:
    load_env()
    # Start the in-container live agent servers (hosted agent :8088, A2A Agent B
    # :8089). Best-effort — never block or crash startup if they can't bind.
    try:
        from . import live_agents

        live_agents.start_servers()
    except Exception:  # noqa: BLE001
        pass


@app.get("/api/demos")
def list_demos() -> JSONResponse:
    return JSONResponse([_demo_payload(demo) for demo in CATALOG])


@app.get("/api/models")
def list_models(tools: bool = False) -> JSONResponse:
    from . import inference

    return JSONResponse({"models": inference.list_models(tools_only=tools),
                         "default": inference.DEFAULT_MODEL})


@app.get("/api/environment")
def get_environment(refresh: bool = False) -> JSONResponse:
    return JSONResponse(environment_summary(refresh=refresh))


@app.get("/api/config")
def get_config() -> JSONResponse:
    return JSONResponse(current_config())


@app.post("/api/config")
async def set_config(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        body = {}
    return JSONResponse(update_config(body or {}))


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


@app.get("/api/demos/{demo_id}/code")
def demo_code(demo_id: str) -> JSONResponse:
    res = get_code(demo_id)
    if res is None:
        return JSONResponse({"error": "unknown demo"}, status_code=404)
    return JSONResponse(res)


# Static SPA last, so /api/* routes win.
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
