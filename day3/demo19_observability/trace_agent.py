#!/usr/bin/env python3
"""
Day 3 · Demo 19 — Govern the AI lifecycle with observability  (Module 7)
=======================================================================
The Foundry **Control Plane** governs agents with *observability* — health,
cost, token usage and behavior per agent. Underneath, that observability is
**OpenTelemetry**: every model call, tool call and agent step becomes a span
with timing + token attributes, exported to **Application Insights**.

This demo instruments a small multi-step agent run with OpenTelemetry and prints
the resulting span tree (operation · duration · tokens). If
`APPLICATIONINSIGHTS_CONNECTION_STRING` is set and `azure-monitor-opentelemetry`
is installed, the same spans also export to Application Insights — exactly what
the Observability pane reads.

Slide source:
  https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-agents-sdk

Prereqs:
  pip install opentelemetry-sdk azure-ai-inference azure-identity python-dotenv
  pip install azure-monitor-opentelemetry      # optional, for App Insights export
  az login
Env:
  FOUNDRY_ACCOUNT_ENDPOINT               Azure OpenAI / model-inference endpoint
  MODEL_DEPLOYMENT_NAME                  chat deployment (default gpt-4o)
  APPLICATIONINSIGHTS_CONNECTION_STRING  optional — turns on cloud export
"""
from __future__ import annotations
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, DIM, RESET

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


def _setup_tracing() -> InMemorySpanExporter:
    provider = TracerProvider()
    memory = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(memory))

    # Optional: export the very same spans to Application Insights.
    conn = env("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if conn:
        try:
            from azure.monitor.opentelemetry import configure_azure_monitor
            configure_azure_monitor(connection_string=conn)
            rule("Azure Monitor export ON — spans will appear in Application Insights.", "ok")
        except ImportError:
            rule("azure-monitor-opentelemetry not installed — local spans only.", "warn")

    trace.set_tracer_provider(provider)
    return memory


def _chat(deployment: str, system: str, user: str) -> tuple[str, int]:
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import SystemMessage, UserMessage
    from azure.identity import DefaultAzureCredential

    base = (env("FOUNDRY_ACCOUNT_ENDPOINT") or "").rstrip("/")
    endpoint = base if base.endswith("/models") else base + "/models"
    client = ChatCompletionsClient(
        endpoint=endpoint, credential=DefaultAzureCredential(),
        credential_scopes=["https://cognitiveservices.azure.com/.default"],
        api_version="2024-05-01-preview",
    )
    res = client.complete(messages=[SystemMessage(content=system), UserMessage(content=user)],
                          model=deployment)
    tokens = getattr(getattr(res, "usage", None), "total_tokens", 0) or 0
    return res.choices[0].message.content or "", tokens


def main() -> None:
    load_env()
    banner("Day 3 · Demo 19 — Agent observability with OpenTelemetry",
           "spans · token usage · latency → Application Insights")
    deployment = env("MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    env("FOUNDRY_ACCOUNT_ENDPOINT", required=True)

    memory = _setup_tracing()
    tracer = trace.get_tracer("accelerate.agentic.demo19")

    question = "What's a good 3-item travel checklist for Reykjavik in winter?"
    rule(f"Running a traced agent for: {question!r}", "step")

    with tracer.start_as_current_span("agent.invoke") as root:
        root.set_attribute("agent.name", "TravelHelper")
        root.set_attribute("input", question)

        with tracer.start_as_current_span("model.plan") as s1:
            plan, t1 = _chat(deployment,
                             "You plan briefly. Reply in one short sentence.",
                             f"How should I approach answering: {question}")
            s1.set_attribute("gen_ai.request.model", deployment)
            s1.set_attribute("gen_ai.usage.total_tokens", t1)

        with tracer.start_as_current_span("tool.weather_lookup") as s2:
            time.sleep(0.05)  # simulate an external tool call
            weather = "Reykjavik winter: -2°C, windy, icy roads, ~5h daylight."
            s2.set_attribute("tool.name", "weather_lookup")
            s2.set_attribute("tool.output", weather)

        with tracer.start_as_current_span("model.answer") as s3:
            answer, t3 = _chat(deployment,
                               "You are a concise travel assistant.",
                               f"{question}\nContext: {weather}\nPlan: {plan}")
            s3.set_attribute("gen_ai.request.model", deployment)
            s3.set_attribute("gen_ai.usage.total_tokens", t3)
        root.set_attribute("output", answer)

    print(f"\n{DIM}Agent answer:{RESET} {answer}\n")

    rule("Captured spans (operation · duration · tokens):", "info")
    spans = sorted(memory.get_finished_spans(), key=lambda s: s.start_time)
    total_tokens = total_ms = 0
    for sp in spans:
        ms = (sp.end_time - sp.start_time) / 1e6
        tok = sp.attributes.get("gen_ai.usage.total_tokens", 0) or 0
        total_ms = max(total_ms, ms) if sp.name == "agent.invoke" else total_ms
        total_tokens += int(tok)
        rule(f"  {sp.name:<22} {ms:7.1f} ms   tokens={tok}", "step")
    rule(f"Total tokens={total_tokens} · end-to-end≈{total_ms:.0f} ms", "ok")
    rule("Set APPLICATIONINSIGHTS_CONNECTION_STRING to stream these to the "
         "Control Plane Observability pane.", "info")


if __name__ == "__main__":
    main()
