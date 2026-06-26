"""Server-Sent Events plumbing.

The demos are synchronous Azure SDK calls. To stream their progress (status
lines, Foundry-side objects, streamed tokens) to the browser, each demo runs in
a worker thread and pushes typed events into a queue that an async generator
drains as an SSE stream.

Event protocol (event name -> data):
  status   {message, kind?}            a step/progress line
  foundry  {label, value?, kind?, ...} something that happened on the Foundry side
  token    {text}                      a streamed answer delta
  answer   {text, role?}               a full message (user or agent)
  metric   {label, value, unit?}       a number worth showing (tokens, latency)
  severity {category, severity, max?}  guardrail harm score
  citation {ref_id, title?, text?, page?}  a retrieval citation
  subquery {text}                      an agentic-retrieval planned subquery
  error    {message, type?, hint?}     a failure (non-fatal to the server)
  done     {}                          stream complete
"""
from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Callable

from starlette.responses import StreamingResponse

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # disable proxy buffering if any
}


def format_sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


class EventStream:
    """Thread-safe event emitter handed to each demo's blocking run()."""

    def __init__(self, loop: asyncio.AbstractEventLoop, queue: "asyncio.Queue") -> None:
        self._loop = loop
        self._q = queue

    def emit(self, event: str, data: dict | None = None) -> None:
        self._loop.call_soon_threadsafe(self._q.put_nowait, (event, data or {}))

    # ---- convenience wrappers -------------------------------------------- #
    def status(self, message: str, kind: str = "info", **extra: Any) -> None:
        self.emit("status", {"message": message, "kind": kind, **extra})

    def foundry(self, label: str, value: Any = None, kind: str = "object", **extra: Any) -> None:
        self.emit("foundry", {"label": label, "value": value, "kind": kind, **extra})

    def token(self, text: str) -> None:
        self.emit("token", {"text": text})

    def answer(self, text: str, role: str = "agent", **extra: Any) -> None:
        self.emit("answer", {"text": text, "role": role, **extra})

    def user(self, text: str) -> None:
        self.emit("answer", {"text": text, "role": "user"})

    def metric(self, label: str, value: Any, unit: str = "") -> None:
        self.emit("metric", {"label": label, "value": value, "unit": unit})

    def severity(self, category: str, severity: int, max_severity: int = 7) -> None:
        self.emit("severity", {"category": category, "severity": severity, "max": max_severity})

    def citation(self, ref_id: str, title: str = "", text: str = "", page: Any = None) -> None:
        self.emit("citation", {"ref_id": ref_id, "title": title, "text": text, "page": page})

    def subquery(self, text: str) -> None:
        self.emit("subquery", {"text": text})

    def error(self, message: str, type: str = "Error", hint: str = "") -> None:
        self.emit("error", {"message": message, "type": type, "hint": hint})


def sse_stream(run_blocking: Callable[[EventStream], None]) -> StreamingResponse:
    """Run `run_blocking(stream)` in a worker thread; serve its events as SSE."""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue = asyncio.Queue()
    stream = EventStream(loop, queue)
    _DONE = object()

    def worker() -> None:
        try:
            run_blocking(stream)
        except Exception as exc:  # noqa: BLE001 - surface, don't crash the server
            stream.error(str(exc), type=type(exc).__name__)
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, (_DONE, None))

    threading.Thread(target=worker, daemon=True).start()

    async def generator():
        # Initial comment flushes headers in some browsers immediately.
        yield ": stream open\n\n"
        while True:
            event, data = await queue.get()
            if event is _DONE:
                yield format_sse("done", {})
                break
            yield format_sse(event, data)

    return StreamingResponse(generator(), media_type="text/event-stream", headers=_SSE_HEADERS)
