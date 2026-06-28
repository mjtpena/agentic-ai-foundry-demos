"""Day 1 · Demo 4 — Deploy your first hosted agent (slide 87).

The hosted agent runs as a local web server on :8088 (`azd ai agent run` inside
day1/demo4_hosted_agent). This page checks whether that server is up and, if so,
invokes it; otherwise it shows how to start it. The point of the demo is that the
SAME code runs locally and, via `azd deploy`, on Foundry Agent Service.
"""
from __future__ import annotations

from ..sse import EventStream

LOCAL_URL = "http://127.0.0.1:8088"
CANDIDATE_PATHS = ["/responses", "/v1/responses", "/invoke"]
START_HINT = ("Start it in another terminal:\n"
              "  cd day1/demo4_hosted_agent\n"
              "  azd ai agent run        # serves this agent on :8088")


def _probe() -> bool:
    import httpx

    for path in ("/health", "/", "/openapi.json"):
        try:
            r = httpx.get(LOCAL_URL + path, timeout=1.5)
            if r.status_code < 500:
                return True
        except Exception:
            continue
    return False


def status() -> dict:
    up = _probe()
    return {"ready": up, "url": LOCAL_URL,
            "reason": None if up else "local hosted-agent server (:8088) is not running"}


def run(stream: EventStream, payload: dict) -> None:
    import httpx

    stream.foundry("Hosted endpoint", LOCAL_URL, kind="hosting")
    message = (payload or {}).get("message") or "What time is it in Tokyo, and how long until 6pm there?"
    stream.user(message)

    # Try local hosted agent server first; if unavailable, provide an in-process
    # fallback implementation for common demo queries so the UI demo remains
    # functional when the local server isn't running (e.g., in cloud deploy).
    if _probe():
        stream.status("Invoking the local hosted agent (server-side Python tools)…", kind="step")
        body = {"input": message, "stream": False}
        last_err = None
        with httpx.Client(timeout=60) as client:
            for path in CANDIDATE_PATHS:
                try:
                    r = client.post(LOCAL_URL + path, json=body)
                    if r.status_code >= 400:
                        last_err = f"{path} → HTTP {r.status_code}"
                        continue
                    data = r.json()
                    text = (data.get("output_text")
                            or _dig_text(data)
                            or r.text)
                    stream.foundry("Served by", path, kind="hosting")
                    stream.answer(text)
                    return
                except Exception as exc:  # noqa: BLE001
                    last_err = f"{path} → {type(exc).__name__}: {exc}"
                    continue
        stream.error(f"Could not invoke the local agent ({last_err}).",
                     hint="Use `azd ai agent invoke --local \"...\"` from day1/demo4_hosted_agent, "
                          "or check the server's API path.")
        return

    # Fallback: simple in-process responder for demo-friendly queries (Tokyo/time)
    stream.status("Local hosted agent not reachable — using simulated fallback.", kind="warn")
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime

        text = ""
        msg_l = message.lower()
        if "tokyo" in msg_l:
            tz = ZoneInfo("Asia/Tokyo")
            now = datetime.now(tz)
            text = f"The current date and time in Tokyo is {now.strftime('%A, %B %d, %Y at %I:%M %p %Z')}"
            # if asking until 6pm
            if "6pm" in msg_l or "6 pm" in msg_l:
                target = now.replace(hour=18, minute=0, second=0, microsecond=0)
                delta_h = (target - now).total_seconds() / 3600
                if delta_h < 0:
                    delta_h += 24
                text += f"\nAbout {delta_h:.1f} hours until 18:00 in Tokyo. (Simulated response)"
        else:
            # generic simulated reply
            text = (
                "(Simulated hosted agent) I couldn't reach a local hosted-agent server, "
                "so returning a demo-friendly placeholder response. For full behavior, "
                "run the hosted agent locally with: cd day1/demo4_hosted_agent && azd ai agent run"
            )
        stream.foundry("Fallback responder", "in-process simulation", kind="hosting")
        stream.answer(text)
    except Exception as exc:  # noqa: BLE001
        stream.error(f"Fallback responder failed: {exc}")


def _dig_text(data) -> str | None:
    """Best-effort extraction of the assistant text from a Responses-style payload."""
    try:
        out = data.get("output") or data.get("response", {}).get("output")
        if isinstance(out, list):
            for item in out:
                for c in item.get("content", []):
                    if c.get("type") in ("output_text", "text") and c.get("text"):
                        return c["text"]
    except Exception:
        pass
    return None
