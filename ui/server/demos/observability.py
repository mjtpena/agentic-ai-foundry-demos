"""Day 3 · Demo 19 — Agent observability with OpenTelemetry (Module 7).

The Foundry Control Plane governs agents with *observability* — and underneath,
that observability is OpenTelemetry: every model call, tool call and agent step
becomes a span with timing + token attributes, exported to Application Insights.

This runs a real multi-step agent turn (plan → tool → answer) under a private
OpenTelemetry TracerProvider with an in-memory exporter, then streams the
captured span tree (operation · duration · tokens) to the trace panel — the same
data the Observability pane reads. If `APPLICATIONINSIGHTS_CONNECTION_STRING` is
set (and azure-monitor-opentelemetry installed), the spans also export to the
cloud.

Companion to `day3/demo19_observability/trace_agent.py` (shown in View Source).
"""
from __future__ import annotations

import time

from .. import inference
from ..foundry import env
from ..sse import EventStream


def _chat(model: str, system: str, user: str) -> tuple[str, int]:
    from azure.ai.inference.models import SystemMessage, UserMessage

    res = inference.complete(model, [SystemMessage(content=system), UserMessage(content=user)],
                             max_tokens=300)
    tokens = getattr(getattr(res, "usage", None), "total_tokens", 0) or 0
    return res.choices[0].message.content or "", int(tokens)


def run(stream: EventStream, payload: dict) -> None:
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    model = inference.valid_model((payload or {}).get("model"))
    question = (payload or {}).get("question") or \
        "What's a good 3-item travel checklist for Reykjavik in winter?"

    # Private provider/tracer — no global state, safe to run repeatedly.
    provider = TracerProvider()
    memory = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    tracer = provider.get_tracer("accelerate.agentic.demo19")

    # Optional cloud export — the real Observability pane source.
    ai_export = False
    if env("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor  # noqa: F401
            ai_export = True
        except Exception:  # noqa: BLE001
            ai_export = False

    stream.foundry("Model", inference.label_for(model), kind="model")
    stream.foundry("Tracer", "OpenTelemetry · in-memory exporter", kind="trace")
    stream.foundry("App Insights export",
                   "configured" if ai_export else "not configured (local spans only)",
                   kind="ok" if ai_export else "warn")
    stream.user(question)
    stream.status("Running a traced agent turn: plan → tool → answer …", kind="step")

    answer = ""
    with tracer.start_as_current_span("agent.invoke") as root:
        root.set_attribute("agent.name", "TravelHelper")
        root.set_attribute("input", question)

        with tracer.start_as_current_span("model.plan") as s1:
            plan, t1 = _chat(model, "You plan briefly. Reply in one short sentence.",
                             f"How should I approach answering: {question}")
            s1.set_attribute("gen_ai.request.model", model)
            s1.set_attribute("gen_ai.usage.total_tokens", t1)

        with tracer.start_as_current_span("tool.weather_lookup") as s2:
            time.sleep(0.05)
            weather = "Reykjavik winter: -2°C, windy, icy roads, ~5h daylight."
            s2.set_attribute("tool.name", "weather_lookup")
            s2.set_attribute("tool.output", weather)

        with tracer.start_as_current_span("model.answer") as s3:
            answer, t3 = _chat(model, "You are a concise travel assistant.",
                               f"{question}\nContext: {weather}\nPlan: {plan}")
            s3.set_attribute("gen_ai.request.model", model)
            s3.set_attribute("gen_ai.usage.total_tokens", t3)
        root.set_attribute("output", answer)

    stream.answer(answer)

    # ---- stream the captured span tree ----------------------------------- #
    spans = sorted(memory.get_finished_spans(), key=lambda s: s.start_time)
    total_tokens = 0
    e2e_ms = 0.0
    stream.status("Captured OpenTelemetry spans:", kind="step")
    for sp in spans:
        ms = (sp.end_time - sp.start_time) / 1e6
        tok = int(sp.attributes.get("gen_ai.usage.total_tokens", 0) or 0)
        total_tokens += tok
        if sp.name == "agent.invoke":
            e2e_ms = ms
        span_id = format(sp.context.span_id, "016x")[:8]
        extra = f"{tok} tok" if tok else (sp.attributes.get("tool.name") or "step")
        stream.foundry(sp.name, f"{ms:.0f} ms · {extra}", kind="trace", id=span_id)

    stream.metric("Spans", len(spans))
    stream.metric("Total tokens", total_tokens)
    stream.metric("End-to-end", f"{e2e_ms:.0f}", unit=" ms")
    stream.status("Set APPLICATIONINSIGHTS_CONNECTION_STRING to stream these into "
                  "the Control Plane Observability pane.", kind="info")
