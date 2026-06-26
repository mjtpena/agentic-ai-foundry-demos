# Day 1 · Demo 4 — Deploy your first hosted agent

**Slides 86-87.** A hosted agent is *code you write* (the orchestration logic and
tools) that Foundry runs as a managed container on Agent Service. The
**hosting adapter** (`from_agent_framework`) turns your agent into the Foundry
Responses API on `localhost:8088` so you can test locally, then `azd deploy`
ships the identical code to the cloud.

### What's here
| File | Role |
|---|---|
| `agent.py` | The agent. Two **local Python tools** (`get_local_date_time`, `hours_until`) so it demonstrates real tool *selection*, wrapped by the hosting adapter. |
| `azure.yaml` | azd config (`startupCommand: python agent.py`). |
| `requirements.txt` | `agent-framework`, the agentserver hosting adapter, identity, dotenv. |
| `setup.sh` | The slide-87 flow end-to-end (install ext → init → provision → run → invoke → deploy). |

### Run it
```bash
cd day1/demo4_hosted_agent
./setup.sh            # walks the azd steps interactively
```
Or manually, exactly as the slide lists:
```bash
azd ext install azure.ai.agents
azd ai agent init                 # Start new from a template; deployment name = gpt-4.1
azd provision
azd ai agent run                  # serves agent.py on :8088
# in a second terminal:
azd ai agent invoke --local "What time is it in Tokyo, and how long until 9am there?"
azd deploy                        # build remotely + deploy to Agent Service
azd ai agent monitor              # live logs
azd down                          # CLEAN UP — stops charges
```

### Troubleshooting (from the slide)
| Error | Fix |
|---|---|
| `DefaultAzureCredential` failure | `azd auth login` again |
| `ResourceNotFound` | endpoint URLs must match the Foundry portal |
| `DeploymentNotFound` | check the deployment name under Build › Deployments |
| Connection refused | port 8088 already in use |

> Hosted agents are in preview and **incur charges while deployed** — run `azd down` when done.
