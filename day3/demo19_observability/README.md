# Day 3 · Demo 19 — Govern the AI lifecycle with observability

> Module 7 · "Foundry Control Plane — govern the AI lifecycle with observability"

The Control Plane's Observability pane (health, cost, token usage, behavior per
agent) is built on **OpenTelemetry**: every model call, tool call and agent step
becomes a **span** with timing + token attributes, exported to **Application
Insights**.

This demo instruments a small multi-step agent turn (**plan → tool → answer**)
with OpenTelemetry and shows the resulting span tree — operation, duration,
tokens. Point it at Application Insights and the same spans flow straight into
the Observability pane.

## Run it
```bash
pip install opentelemetry-sdk azure-ai-inference azure-identity python-dotenv
pip install azure-monitor-opentelemetry      # optional — App Insights export
az login
python day3/demo19_observability/trace_agent.py
```

Env:
- `FOUNDRY_ACCOUNT_ENDPOINT` — model-inference endpoint
- `MODEL_DEPLOYMENT_NAME` — chat deployment (default `gpt-4o`)
- `APPLICATIONINSIGHTS_CONNECTION_STRING` *(optional)* — turns on cloud export

## In the live console
The UI demo (**Day 3 · Observability**) runs the same traced turn under a private
OpenTelemetry provider with an in-memory exporter and streams the captured spans
to the Foundry-trace panel — no preview package required. **View Source** there
shows this script.

Reference:
https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/trace-agents-sdk
