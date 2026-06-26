# Day 2 · Demo 8 — Add an A2A agent endpoint (slide 35, preview)

A Foundry agent with an **A2ATool** that calls a secondary A2A-compatible agent
through a project connection and streams the response back.

```bash
# 1) create the A2A connection to your secondary agent
A2A_TARGET_URL="https://my-secondary-agent.example.com/a2a" ./setup_a2a_connection.sh
# 2) paste the printed connection id into ../../.env as A2A_PROJECT_CONNECTION_ID
pip install "azure-ai-projects[agents]" python-dotenv azure-identity
az login
python a2a_agent.py
```
`a2a_agent.py` keeps the slide's full streaming event handling (`response.created`,
deltas, `remote_function_call`, completion) and cleans up the agent version.

> A2A connects to **non-Microsoft** endpoints you trust. Review what data you
> share; Microsoft doesn't test third-party A2A endpoints (slide's note).

Env: `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL_DEPLOYMENT_NAME`, `A2A_PROJECT_CONNECTION_ID`.
Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/agent-to-agent
