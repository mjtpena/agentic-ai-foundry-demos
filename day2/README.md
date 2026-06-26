# Day 2 — Extend, ground and orchestrate intelligent agents

| # | Demo | Slide | Type | Folder / file |
|---|---|---|---|---|
| 5 | Explore the Foundry Tools | 16 | Portal | `demo5_explore_foundry_tools.md` |
| 6 | **Connect MCP tools to agents** | 27 | Python | `demo6_mcp_agent/` |
| 7 | **Connect to an OpenAPI Specification** | 30 | Python | `demo7_openapi_tool/` |
| 8 | **Add an A2A agent endpoint** | 35 | Python | `demo8_a2a_agent/` |
| 9 | **Create a knowledge source** | 51 | Python | `demo9_10_agentic_retrieval/` |
| 10 | Agentic retrieval (portal) | 61 | Python + Portal | `demo9_10_agentic_retrieval/portal_runbook.md` |
| 11 | Unified Work/Fabric/Foundry IQ | 69 | Runbook | `demo11_unified_iq.md` |
| 12 | **Create and run an agent with Agent Framework** | 83 | Python | `demo12_agent_framework/` |

```bash
# from repo root, after provisioning + pip install -r requirements.txt
python day2/demo6_mcp_agent/client.py
python day2/demo7_openapi_tool/openapi_agent.py
python day2/demo12_agent_framework/joker_agent.py
# agentic retrieval (3 steps, in order):
infra/upload_sample_data.sh
python day2/demo9_10_agentic_retrieval/01_create_knowledge_source.py
python day2/demo9_10_agentic_retrieval/02_create_knowledge_base.py
python day2/demo9_10_agentic_retrieval/03_query_knowledge_base.py
```
