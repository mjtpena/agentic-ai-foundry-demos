"""Shared Foundry helpers: .env loading, credentials, and a live environment
summary the UI shows in its sidebar (what's actually provisioned on Foundry).

Everything here is best-effort and defensive: a missing az CLI, a slow Azure
call, or an absent env var degrades to a clear, non-fatal state instead of
crashing the server.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]

# Make `from shared.console import ...` importable for the demo wrappers.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# --------------------------------------------------------------------------- #
# .env loading
# --------------------------------------------------------------------------- #
_ENV_LOADED = False


def load_env() -> None:
    """Load the repo-root .env (written by infra/provision) into os.environ once."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = REPO_ROOT / ".env"
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path, override=False)
        load_dotenv(REPO_ROOT / ".env.local", override=True)
    except ImportError:  # pragma: no cover - minimal fallback parser
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
    _ENV_LOADED = True


def env(name: str, *fallbacks: str, default: str | None = None) -> str | None:
    """First non-empty value among name + fallbacks, else default."""
    for key in (name, *fallbacks):
        val = os.environ.get(key)
        if val:
            return val
    return default


# --------------------------------------------------------------------------- #
# Runtime configuration (the UI "Foundry configuration" modal)
# --------------------------------------------------------------------------- #
# Maps the modal's field keys to the canonical environment variables the demos
# read. Saving applies values to the live process and persists them to
# .env.local (which load_env() loads with override=True on the next read).
CONFIG_KEYS: dict[str, str] = {
    "project_endpoint": "PROJECT_ENDPOINT",
    "account_endpoint": "FOUNDRY_ACCOUNT_ENDPOINT",
    "search_endpoint": "SEARCH_ENDPOINT",
    "a2a_connection_id": "A2A_PROJECT_CONNECTION_ID",
}


def current_config() -> dict:
    """Current value of each configurable endpoint, for pre-filling the modal."""
    load_env()
    return {ui_key: os.environ.get(env_key, "") for ui_key, env_key in CONFIG_KEYS.items()}


def update_config(values: dict) -> dict:
    """Apply config from the UI: set live os.environ and persist to .env.local.

    Empty fields are ignored (existing values are preserved, never cleared).
    """
    global _ENV_SUMMARY_CACHE
    load_env()
    applied: dict[str, str] = {}
    for ui_key, env_key in CONFIG_KEYS.items():
        if ui_key not in values:
            continue
        val = (values.get(ui_key) or "").strip()
        if val:
            os.environ[env_key] = val
            applied[env_key] = val
    if applied:
        _persist_env_local(applied)
        _ENV_SUMMARY_CACHE = None  # force the sidebar to rebuild on next read
    return {"ok": True, "applied": sorted(applied), "config": current_config()}


def _persist_env_local(values: dict) -> None:
    """Merge KEY=value pairs into REPO_ROOT/.env.local, preserving other lines."""
    path = REPO_ROOT / ".env.local"
    out: list[str] = []
    seen: set[str] = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in values:
                    out.append(f"{key}={values[key]}")
                    seen.add(key)
                    continue
            out.append(line)
    for key, val in values.items():
        if key not in seen:
            out.append(f"{key}={val}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def get_credential():
    """DefaultAzureCredential — works from the signed-in az CLI session."""
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential()


# --------------------------------------------------------------------------- #
# Small az CLI helper (cached) — used only for the read-only environment panel
# --------------------------------------------------------------------------- #
_AZ_CACHE: dict[str, tuple[float, Any]] = {}
_AZ_LOCK = threading.Lock()
_AZ_TTL = 120.0  # seconds


def _az(*args: str, ttl: float = _AZ_TTL) -> Any:
    """Run `az ... -o json` and return parsed JSON, cached. None on any failure."""
    key = " ".join(args)
    now = time.time()
    with _AZ_LOCK:
        hit = _AZ_CACHE.get(key)
        if hit and now - hit[0] < ttl:
            return hit[1]
    value = None
    try:
        # shell=True so Windows resolves az.cmd; args are static/local, not user input.
        proc = subprocess.run(
            "az " + " ".join(args) + " -o json",
            shell=True,
            capture_output=True,
            text=True,
            timeout=25,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            value = json.loads(proc.stdout)
    except Exception:
        value = None
    with _AZ_LOCK:
        _AZ_CACHE[key] = (now, value)
    return value


def _account_name_from_endpoint(endpoint: str | None) -> str | None:
    """foundry-aa-xxx from https://foundry-aa-xxx.services.ai.azure.com/..."""
    if not endpoint:
        return None
    host = urlparse(endpoint).hostname or ""
    return host.split(".")[0] or None


def _project_name_from_endpoint(endpoint: str | None) -> str | None:
    if not endpoint:
        return None
    parts = urlparse(endpoint).path.strip("/").split("/")
    # .../api/projects/<project>
    if "projects" in parts:
        i = parts.index("projects")
        if i + 1 < len(parts):
            return parts[i + 1]
    return None


# --------------------------------------------------------------------------- #
# Environment summary (the sidebar)
# --------------------------------------------------------------------------- #
_ENV_SUMMARY_CACHE: tuple[float, dict] | None = None


def environment_summary(refresh: bool = False) -> dict:
    """Build the live 'Foundry Environment' panel. Cached ~2 min."""
    global _ENV_SUMMARY_CACHE
    load_env()
    now = time.time()
    if _ENV_SUMMARY_CACHE and not refresh and now - _ENV_SUMMARY_CACHE[0] < _AZ_TTL:
        return _ENV_SUMMARY_CACHE[1]

    project_endpoint = env("PROJECT_ENDPOINT", "FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_PROJECT_ENDPOINT")
    account_endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT")
    search_endpoint = env("SEARCH_ENDPOINT", "AZURE_SEARCH_ENDPOINT")

    account_name = _account_name_from_endpoint(account_endpoint or project_endpoint)
    project_name = _project_name_from_endpoint(project_endpoint)

    # Identity / subscription (cheap, single az call)
    acct = _az("account", "show") or {}
    subscription = {
        "name": acct.get("name"),
        "id": acct.get("id"),
        "tenant": acct.get("tenantDefaultDomain") or acct.get("tenantId"),
        "user": (acct.get("user") or {}).get("name"),
        "state": acct.get("state"),
    }

    # Resource group + region + deployed models (best-effort)
    resource_group = None
    region = None
    models: list[dict] = []
    if account_name:
        found = _az("cognitiveservices", "account", "list",
                    "--query", f"\"[?name=='{account_name}'].{{rg:resourceGroup,location:location}}\"")
        if isinstance(found, list) and found:
            resource_group = found[0].get("rg")
            region = found[0].get("location")
        if resource_group:
            deps = _az("cognitiveservices", "account", "deployment", "list",
                       "-n", account_name, "-g", resource_group)
            if isinstance(deps, list):
                for d in deps:
                    props = d.get("properties", {})
                    sku = d.get("sku", {}) or {}
                    models.append({
                        "name": d.get("name"),
                        "version": (props.get("model", {}) or {}).get("version"),
                        "sku": sku.get("name"),
                        "capacity": sku.get("capacity"),
                        "state": props.get("provisioningState"),
                    })

    # Cloud fallback: a container has no az CLI — fill the panel from env vars.
    subscription["name"] = subscription["name"] or env("ENV_SUBSCRIPTION_NAME")
    subscription["id"] = subscription["id"] or env("ENV_SUBSCRIPTION_ID")
    subscription["tenant"] = subscription["tenant"] or env("ENV_TENANT")
    subscription["user"] = subscription["user"] or env("ENV_IDENTITY", default="managed identity")
    subscription["state"] = subscription["state"] or ("Enabled" if subscription["name"] else None)
    resource_group = resource_group or env("ENV_RESOURCE_GROUP")
    region = region or env("ENV_REGION")
    if not models:
        for _nm in (env("FOUNDRY_MODELS", default="") or "").split(","):
            _nm = _nm.strip()
            if _nm:
                models.append({"name": _nm, "state": "Succeeded",
                               "version": None, "sku": None, "capacity": None})

    # Which model names the demos actually reference, so we can flag fallbacks.
    referenced = {
        "chat": env("MODEL_DEPLOYMENT_NAME", default="gpt-4o"),
        "prompt_agent": env("PROMPT_AGENT_MODEL", default="gpt-5-mini"),
        "hosted_agent": env("HOSTED_AGENT_MODEL", default="gpt-4.1"),
        "embedding": env("EMBEDDING_DEPLOYMENT", default="text-embedding-3-large"),
    }
    deployed_names = {m["name"] for m in models if m.get("name")}
    for role, name in referenced.items():
        if models and name not in deployed_names:
            models.append({"name": name, "state": "NotDeployed", "referenced_by": role,
                           "version": None, "sku": None, "capacity": None})

    portal = _portal_links(subscription.get("id"), resource_group, account_name,
                           project_name, subscription.get("tenant"))

    summary = {
        "project": {"name": project_name, "endpoint": project_endpoint},
        "account": {"name": account_name, "endpoint": account_endpoint, "region": region,
                    "resource_group": resource_group},
        "subscription": subscription,
        "identity": {
            "user": subscription.get("user"),
            "tenant": subscription.get("tenant"),
            "credential": "DefaultAzureCredential (az login)",
        },
        "models": models,
        "referenced_models": referenced,
        "search": {"endpoint": search_endpoint,
                   "service": _account_name_from_endpoint(search_endpoint)},
        "storage": {"account": env("STORAGE_ACCOUNT"), "container": env("BLOB_CONTAINER")},
        "mcp": {"url": env("MCP_SERVER_URL"), "label": env("MCP_SERVER_LABEL")},
        "a2a": {"connection_id": env("A2A_PROJECT_CONNECTION_ID")},
        "portal": portal,
        "fetched_at": now,
    }
    _ENV_SUMMARY_CACHE = (now, summary)
    return summary


def _portal_links(sub_id, rg, account, project, tenant) -> dict:
    links: dict[str, str] = {"foundry": "https://ai.azure.com/"}
    if sub_id and rg:
        base = f"https://portal.azure.com/#@{tenant or ''}/resource/subscriptions/{sub_id}/resourceGroups/{rg}"
        links["resource_group"] = f"{base}/overview"
        if account:
            links["account"] = (
                f"{base}/providers/Microsoft.CognitiveServices/accounts/{account}/overview"
            )
    return links
