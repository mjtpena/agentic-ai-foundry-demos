# Foundry Live Demo Console

A branded web UI for the *Accelerate Agentic AI* demos. It drives the **same
Microsoft Foundry SDK calls** as the Day 1–3 console scripts, but renders each
run visually — the agent's response **and** what happened on the Foundry side
(agents, tool calls, run steps, retrieval plans, guardrail verdicts) — so the
capability is legible to an audience instead of scrolling past in a terminal.

Design language follows **Fluent 2** (Segoe UI Variable, Azure `#0f6cbd`, flat
surfaces, hairline borders) so it reads like a Microsoft tool, not a generic app.

## Run it

```powershell
# prerequisites: infra/provision.ps1 has written ../.env, and you're signed in
az login
.\ui\run.ps1            # -> http://127.0.0.1:8099
```

```bash
./ui/run.sh            # macOS / Linux / WSL -> http://127.0.0.1:8099
```

Both use the repo's `.venv`. If you haven't created it:

```
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -r ui/requirements-ui.txt
.\.venv\Scripts\python -m pip install --pre "azure-ai-projects[agents]" azure-ai-agents
```

> Open the **served URL** (`127.0.0.1:8099`) — not the static `index.html` file.
> The app is backend-driven; the file on its own renders an empty shell.

## The eight demos

| Demo | Shows | State |
|---|---|---|
| Prompt Agent (D1·3) | Multi-turn conversation memory | ready |
| Hosted Agent (D1·4) | Code-based agent + local tools | needs `azd ai agent run` on :8088 |
| MCP Tools (D2·6) | Live tool-use over the MS Learn MCP server | ready |
| OpenAPI Tool (D2·7) | Calling a live REST API from a spec | ready |
| A2A Agent (D2·8) | Agent-to-agent calls | needs an A2A project connection |
| Agentic Retrieval (D2·9/10) | Query planning + grounded citations | click **Set up knowledge base** once |
| Agent Framework (D2·12) | Streaming · `ai_function` tools · `AgentSession` memory | ready |
| Guardrails (D3·16) | Content Safety harms · blocklist · prompt shield | ready |

The two gated demos and the retrieval setup show inline instructions in the UI.

## How it works

```
ui/
  server/                FastAPI app
    main.py              routes: /api/environment, /api/demos, /api/demos/<id>/<action>
    foundry.py           .env + DefaultAzureCredential + live environment summary (az)
    sse.py               runs each blocking demo in a thread, streams typed events as SSE
    catalog.py           demo metadata (nav, badges, slide #)
    demos/<id>.py        thin wrappers around the existing Day 1-3 SDK calls
  web/                   vanilla HTML/CSS/JS (no build step)
    index.html  styles.css  app.js
```

Each demo wrapper emits a small typed event stream (`status`, `foundry`, `token`,
`answer`, `metric`, `severity`, `citation`, `subquery`, `verdict`) that the
front-end turns into the conversation, the **Foundry trace** panel, metrics,
severity gauges and citations. SDK imports live *inside* each wrapper, so a
missing preview package degrades one demo rather than the whole server.

Notes:
- `gpt-5-mini` isn't available in `australiaeast`; the prompt agent uses
  `gpt-4.1-mini` (`PROMPT_AGENT_MODEL` in `.env`).
- Agent Framework targets Azure OpenAI via `OpenAIChatCompletionClient`
  (api-version `2024-10-21`) — the 1.9.x equivalent of `AzureOpenAIChatClient`.
- Prompt Shield needs the preview Content Safety SDK; on the stable build the
  Guardrails demo reports it as unavailable and continues.
