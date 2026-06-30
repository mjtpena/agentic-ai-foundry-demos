#!/usr/bin/env python3
"""
Day 3 · Demo 20 — Secure AI agents with Microsoft Entra ID  (Module 7)
======================================================================
Every demo in this repo authenticates with **DefaultAzureCredential** — no keys,
no secrets in code. That's the foundation of "Secure AI agents with Microsoft
Entra ID": an agent presents an **Entra identity** (a user, a managed identity,
or a first-class **Entra Agent ID**) and gets *exactly* the access RBAC grants
it — least privilege, fully auditable.

This script makes that identity tangible:
  1. acquires an Entra access token (keyless) for the Cognitive Services scope;
  2. decodes the JWT claims so you can see WHO the agent is (appid / oid / tid)
     and WHAT it may call (aud / scp / roles);
  3. lists the RBAC role assignments that identity holds (via `az`).

Slide source:
  https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-azure-ai-foundry

Prereqs:
  pip install azure-identity python-dotenv
  az login        # Azure CLI signed in
"""
from __future__ import annotations
import base64
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, DIM, RESET

SCOPE = "https://cognitiveservices.azure.com/.default"


def _decode_jwt(token: str) -> dict:
    """Decode the (unverified) JWT payload — we only read claims, never trust them."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # restore base64 padding
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:  # noqa: BLE001
        return {}


def main() -> None:
    load_env()
    banner("Day 3 · Demo 20 — Secure AI agents with Microsoft Entra ID",
           "keyless auth · token claims · RBAC role assignments")

    from azure.identity import DefaultAzureCredential
    cred = DefaultAzureCredential()

    rule(f"Acquiring an Entra token for {SCOPE} (keyless)…", "step")
    token = cred.get_token(SCOPE)
    claims = _decode_jwt(token.token)

    oid = claims.get("oid")
    appid = claims.get("appid") or claims.get("azp")
    upn = claims.get("upn") or claims.get("preferred_username") or claims.get("unique_name")
    rule("Identity (who the agent is):", "info")
    rule(f"  principal   {upn or appid or oid}", "ok")
    rule(f"  object id   {oid}", "ok")
    rule(f"  app id      {appid or '—'}", "ok")
    rule(f"  tenant      {claims.get('tid')}", "ok")

    rule("Authorization (what it may call):", "info")
    rule(f"  audience    {claims.get('aud')}", "ok")
    scopes = claims.get("scp") or " ".join(claims.get("roles", [])) or "—"
    rule(f"  scopes      {scopes}", "ok")
    mins = max(0, int((token.expires_on - time.time()) / 60))
    rule(f"  token valid ~{mins} min  ·  No API keys used (keyless). ✓", "ok")

    # RBAC role assignments for this identity (best-effort; needs az + Graph perms).
    if oid:
        rule("RBAC role assignments held by this identity:", "info")
        try:
            out = subprocess.run(
                f'az role assignment list --assignee {oid} --all '
                f'--query "[].{{role:roleDefinitionName, scope:scope}}" -o json',
                shell=True, capture_output=True, text=True, timeout=40)
            roles = json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else []
        except Exception:  # noqa: BLE001
            roles = []
        if roles:
            for r in roles[:8]:
                scope = (r.get("scope") or "").split("/")[-1] or r.get("scope")
                rule(f"  {r.get('role')}  on  {scope}", "ok")
            rule(f"  ({len(roles)} assignment(s) total)", "info")
        else:
            rule("  Couldn't list assignments (az not signed in / insufficient Graph "
                 "permissions). Check the portal runbook.", "warn")

    print()
    rule("This is least-privilege agent access — see portal_runbook.md to register "
         "a first-class Entra Agent ID and assign roles.", "info")
    print(f"{DIM}Module 8 (Agent 365) takes this fleet-wide — see agent365_runbook.md.{RESET}")


if __name__ == "__main__":
    main()
