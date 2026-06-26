# Day 2 · Demo 6 — Connect MCP tools to agents (slide 27)

An agent wired to the public **Microsoft Learn Docs** MCP server, so it answers
developer questions from Microsoft's latest official docs and auto-invokes the
MCP tool (`microsoft_code_sample_search`) without approval prompts.

```bash
pip install azure-ai-projects azure-ai-agents mcp azure-identity
az login
python client.py                                   # default: Container App + managed identity question
python client.py "How do I deploy a Foundry hosted agent?"
```
`client.py` assembles every block the slide walks through (references → connect →
init MCP tool → create agent/thread/message → run → display steps → cleanup),
prints the tool-call trace, and deletes the agent afterward.

Env: `PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME` (gpt-4o), `MCP_SERVER_URL`, `MCP_SERVER_LABEL`.
Reference: https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/03c-use-agent-tools-with-mcp.html
