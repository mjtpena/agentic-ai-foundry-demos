# Accelerate Agentic AI — all 16 demos, end to end

Runnable, slide-faithful implementations of **every demo** across the three-day
*Accelerate Agentic AI* workshop, plus a one-command Azure CLI provisioner that
stands up the shared infrastructure. Built for **Microsoft Foundry** (the new
Foundry), **Copilot Studio**, **Azure AI Search**, **Microsoft Agent Framework**,
and **Foundry Control Plane / Content Safety**.

> Each code demo maps to a specific slide and keeps the slide's exact API calls —
> then goes beyond with real assets, tool-use, memory, cleanup, and polished
> console output. Portal-only demos (Copilot Studio, Control Plane) ship as
> precise click-by-click runbooks.

## 0 · Prerequisites
- **Azure CLI** (`az`) signed in to your subscription: `az login`
- **Azure Developer CLI** (`azd`) — only for Day 1 #4 hosted agent
- **Python 3.10+**
- Permissions to create resources + assign roles in the target subscription
- (Days that touch Copilot Studio / Work IQ / Fabric also need M365 + Fabric)

## 1 · Provision everything (your `az` CLI)
```bash
az login
cd infra
./provision.sh            # bash · macOS/Linux/WSL/Cloud Shell   (or ./provision.ps1)
./upload_sample_data.sh   # Day 2 retrieval sample data
```
This creates the **resource group** `rg-agentic-ai-demos` in **australiaeast**, a
Foundry account + `agentic-demos` project, the model deployments
(`gpt-4o`, `gpt-4.1`, `gpt-4.1-mini`, `gpt-5-mini`, `text-embedding-3-large`),
Azure AI Search, storage, RBAC, and writes a populated `.env`. See
[`infra/README.md`](infra/README.md) for details, region/quota notes, and teardown.

## 2 · Set up Python
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Preview features (Day 2 #6 MCP and #8 A2A) need prerelease builds:
pip install --pre "azure-ai-projects[agents]" azure-ai-agents mcp
```

## 3 · The 16 demos

### Day 1 — Architect intelligent agents with Microsoft IQ and Foundry
| # | Demo | Slide | How to run |
|---|---|---|---|
| 1 | Create and deploy an agent | 56 | runbook · `day1/demo1_copilot_studio_create_agent.md` |
| 2 | Call an agent flow from an agent | 62 | runbook · `day1/demo2_copilot_studio_agent_flow.md` |
| 3 | Create a prompt agent | 84 | `python day1/demo3_prompt_agent/prompt_agent.py` |
| 4 | Deploy your first hosted agent | 87 | `cd day1/demo4_hosted_agent && ./setup.sh` |

### Day 2 — Extend, ground and orchestrate intelligent agents
| # | Demo | Slide | How to run |
|---|---|---|---|
| 5 | Explore the Foundry Tools | 16 | runbook · `day2/demo5_explore_foundry_tools.md` |
| 6 | Connect MCP tools to agents | 27 | `python day2/demo6_mcp_agent/client.py` |
| 7 | Connect to an OpenAPI Specification | 30 | `python day2/demo7_openapi_tool/openapi_agent.py` |
| 8 | Add an A2A agent endpoint | 35 | `day2/demo8_a2a_agent/` (setup script + `a2a_agent.py`) |
| 9 | Create a knowledge source | 51 | `python day2/demo9_10_agentic_retrieval/01_create_knowledge_source.py` |
| 10 | Agentic retrieval (portal) | 61 | `…/02…`, `…/03…` + `portal_runbook.md` |
| 11 | Unified Work/Fabric/Foundry IQ | 69 | runbook · `day2/demo11_unified_iq.md` |
| 12 | Create and run an agent with Agent Framework | 83 | `python day2/demo12_agent_framework/joker_agent.py` |

### Day 3 — Trust, Security, and Control for Enterprise AI Agents
| # | Demo | Slide | How to run |
|---|---|---|---|
| 13 | Foundry Control Plane capabilities | 16 | runbook · `day3/demo13_control_plane.md` |
| 14 | Create a Guardrail policy | 23 | `day3/demo14_guardrail_policy/create_guardrail_policy.sh` |
| 15 | View and fix compliance violations | 26 | runbook · `day3/demo15_fix_compliance_violations.md` |
| 16 | Configure guardrails & controls | 49 | `python day3/demo16_guardrails_content_safety/configure_content_safety.py` |

## 4 · Authentication model
Every Python demo authenticates with **`DefaultAzureCredential`** / **`AzureCliCredential`**
— no keys in code. `provision.sh` grants your signed-in user the needed roles
(Cognitive Services User/OpenAI User, Search data roles, Storage Blob roles). Just
keep `az login` current.

## 5 · Repo layout
```
infra/        provision.sh/.ps1 · upload_sample_data.sh · teardown · 00-variables.sh
shared/       console.py (env loading + pretty output) used by all Python demos
day1/ day2/ day3/   one folder per demo: code + per-demo README + portal runbooks
.env.example  every variable the demos read (provision.sh writes the real .env)
requirements.txt
```

## 6 · Clean up (stop charges)
```bash
infra/teardown.sh        # deletes the whole resource group
# Day 1 #4 also: cd day1/demo4_hosted_agent && azd down
```

## Notes & honesty
- **Region/quota:** `gpt-5-mini` and `gpt-4.1` roll out region-by-region. If a
  deployment can't be created in australiaeast, the provisioner warns and
  continues — `gpt-4o` always deploys and every demo falls back to it via `.env`.
- **Previews:** A2A, hosted agents, and the Search agentic-retrieval objects are
  in preview; class names / api-versions can shift. Each affected demo prints a
  clear message and points to the portal runbook if its SDK surface differs.
- Demos that require Copilot Studio, Work IQ, or Microsoft Fabric are provided as
  runbooks because they're portal/M365 experiences, not `az`/SDK-scriptable.
