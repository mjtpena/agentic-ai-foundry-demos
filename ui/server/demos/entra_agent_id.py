"""Day 3 · Demo 20 — Secure AI agents with Microsoft Entra ID (Module 7).

Makes the keyless trust chain tangible: acquire an Entra access token with
DefaultAzureCredential (no keys), decode its claims to show WHO the agent is
(oid / appid / tenant) and WHAT it may call (audience / scopes), then list the
RBAC role assignments that identity holds. Read-only and safe.

Companion to `day3/demo20_entra_agent_id/inspect_identity.py` (View Source).
"""
from __future__ import annotations

import base64
import json
import time

from ..foundry import _az, env, get_credential
from ..sse import EventStream

SCOPE = "https://cognitiveservices.azure.com/.default"


def _decode_jwt(token: str) -> dict:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:  # noqa: BLE001
        return {}


def run(stream: EventStream, payload: dict) -> None:
    stream.status("Acquiring an Entra access token (keyless) via DefaultAzureCredential…",
                  kind="step")
    try:
        token = get_credential().get_token(SCOPE)
    except Exception as exc:  # noqa: BLE001
        stream.error(f"Could not acquire a token: {exc}",
                     hint="Run `az login` (or configure a managed identity).")
        return

    claims = _decode_jwt(token.token)
    oid = claims.get("oid")
    appid = claims.get("appid") or claims.get("azp")
    upn = (claims.get("upn") or claims.get("preferred_username")
           or claims.get("unique_name") or claims.get("app_displayname"))

    # Identity — who the agent is
    stream.foundry("Principal", upn or appid or oid or "unknown", kind="agent")
    stream.foundry("Object ID (oid)", oid or "—", kind="object")
    stream.foundry("App ID (appid)", appid or "—", kind="object")
    stream.foundry("Tenant (tid)", claims.get("tid") or "—", kind="connection")

    # Authorization — what it may call
    stream.foundry("Audience (aud)", claims.get("aud") or "—", kind="model")
    scopes = claims.get("scp") or " ".join(claims.get("roles", []) or []) or "—"
    stream.foundry("Scopes (scp)", scopes, kind="ok")
    stream.foundry("Auth mode", "keyless — no API keys in code ✓", kind="ok")

    mins = max(0, int((token.expires_on - time.time()) / 60))
    stream.metric("Token valid", mins, unit=" min")

    # RBAC role assignments held by this identity (best-effort via az)
    roles = []
    if oid:
        stream.status("Listing RBAC role assignments for this identity…", kind="step")
        data = _az("role", "assignment", "list", "--assignee", oid, "--all",
                   "--query", "\"[].{role:roleDefinitionName, scope:scope}\"")
        if isinstance(data, list):
            roles = data
    if roles:
        for r in roles[:8]:
            scope = (r.get("scope") or "").rstrip("/").split("/")[-1] or r.get("scope")
            stream.foundry(r.get("role") or "role", f"on {scope}", kind="ok")
        stream.metric("Role assignments", len(roles))
        stream.status(f"Least-privilege access: {len(roles)} role assignment(s), "
                      "all keyless and auditable.", kind="ok")
    else:
        stream.status("Couldn't list role assignments (no az session or insufficient "
                      "Graph permissions) — see portal_runbook.md.", kind="warn")

    stream.answer(
        "This agent authenticates with a Microsoft Entra identity — no keys or "
        "secrets. The token claims above show **who** it is (object id, app id, "
        "tenant) and the RBAC role assignments show **exactly what** it may do. "
        "Remove a role to revoke access; disable the identity to offboard the "
        "agent — the same controls you already use for users. Agent 365 "
        "(Module 8) takes this fleet-wide from the M365 admin center.")
    stream.status("See portal_runbook.md to register a first-class Entra Agent ID; "
                  "agent365_runbook.md for tenant-wide governance.", kind="info")
