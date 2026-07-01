# Foundry Live Demo Console

A branded web UI for the *Accelerate Agentic AI* demos. It drives the **same
Microsoft Foundry SDK calls** as the console scripts, but renders each
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

## Configure your own Foundry environment

The UI reads environment values from repo-root env files (in this order):

1. `.env`
2. `.env.<FOUNDRY_ENVIRONMENT>` (optional)
3. `.env.local`
4. `.env.<FOUNDRY_ENVIRONMENT>.local` (optional)
5. `FOUNDRY_ENV_FILE` (optional extra file, loaded last)

Use these key variables:

- `PROJECT_ENDPOINT` (or `FOUNDRY_PROJECT_ENDPOINT` / `AZURE_AI_PROJECT_ENDPOINT`)
- `FOUNDRY_ACCOUNT_ENDPOINT`
- `SEARCH_ENDPOINT` (or `AZURE_SEARCH_ENDPOINT`)
- `HOSTED_AGENT_ENDPOINT` (defaults to `http://127.0.0.1:8088`)

This makes it easy to keep multiple environments (for example `dev`, `test`, and `prod`) without changing code.

## The eight demos

| Demo | Shows | State |
|---|---|---|
| Prompt Agent (Demo 3) | Multi-turn conversation memory | ready |
| Hosted Agent (Demo 4) | Code-based agent + local tools | needs `azd ai agent run` on :8088 |
| MCP Tools (Demo 6) | Live tool-use over the MS Learn MCP server | ready |
| OpenAPI Tool (Demo 7) | Calling a live REST API from a spec | ready |
| A2A Agent (Demo 8) | Agent-to-agent calls | needs an A2A project connection |
| Agentic Retrieval (Demos 9/10) | Query planning + grounded citations | click **Set up knowledge base** once |
| Agent Framework (Demo 12) | Streaming · `ai_function` tools · `AgentSession` memory | ready |
| Guardrails (Demo 16) | Content Safety harms · blocklist · prompt shield | ready |

The two gated demos and the retrieval setup show inline instructions in the UI.

## How it works

```
ui/
  server/                FastAPI app
    main.py              routes: /api/environment, /api/demos, /api/demos/<id>/<action>
    foundry.py           .env + DefaultAzureCredential + live environment summary (az)
    sse.py               runs each blocking demo in a thread, streams typed events as SSE
    catalog.py           demo metadata (nav, badges, slide #)
    demos/<id>.py        thin wrappers around the existing SDK calls
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
- Agent Framework uses the Foundry model endpoint via `OpenAIChatCompletionClient`
  (api-version `2024-10-21`).
- Prompt Shield needs the preview Content Safety SDK; on the stable build the
  Guardrails demo reports it as unavailable and continues.

## Deploy to Azure (Container Apps)

The console is containerized (root `Dockerfile`) and runs on **Azure Container
Apps** with a **system-assigned managed identity** — no keys. Auth uses
`DefaultAzureCredential`, so the same code runs locally (via `az login`) and in
the cloud (via the managed identity).

```bash
# build + deploy from source (creates an ACR + environment on first run)
az containerapp up -n foundry-demo-console -g rg-agentic-ai-demos -l australiaeast \
  --environment agentic-demos-env --source . --ingress external --target-port 8000 \
  --env-vars PROJECT_ENDPOINT=... FOUNDRY_ACCOUNT_ENDPOINT=... SEARCH_ENDPOINT=... \
             ENV_SUBSCRIPTION_NAME=... ENV_REGION=australiaeast \
             ENV_RESOURCE_GROUP=rg-agentic-ai-demos \
             FOUNDRY_MODELS=gpt-4o,gpt-4.1,gpt-4.1-mini,text-embedding-3-large

# grant the app's identity the same roles your user has
PID=$(az containerapp show -n foundry-demo-console -g rg-agentic-ai-demos --query identity.principalId -o tsv)
FID=$(az cognitiveservices account show -n <foundry-account> -g rg-agentic-ai-demos --query id -o tsv)
SID=$(az search service show -n <search-service> -g rg-agentic-ai-demos --query id -o tsv)
az role assignment create --assignee-object-id $PID --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services User" --scope $FID            # + "Cognitive Services OpenAI User"
az role assignment create --assignee-object-id $PID --assignee-principal-type ServicePrincipal \
  --role "Search Index Data Contributor" --scope $SID      # + Reader + "Search Service Contributor"
```

- The container has no `az` CLI, so the environment sidebar reads `ENV_SUBSCRIPTION_NAME`,
  `ENV_REGION`, `ENV_RESOURCE_GROUP`, and `FOUNDRY_MODELS` from app settings instead.
- **Windows gotcha:** `az containerapp up` may crash streaming the ACR build log
  (a CLI/colorama cp1252 bug) — the image still builds and pushes; just run
  `az containerapp create --image <acr>.azurecr.io/<image>` to finish.
- **Public by default.** Anyone with the URL can run the demos, which call your
  Foundry/Search and incur token cost. Restrict it before sharing widely
  (Container Apps Entra auth via `az containerapp auth`, or IP restrictions).
