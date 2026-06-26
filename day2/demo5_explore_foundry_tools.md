# Day 2 · Demo 5 — Explore the Foundry Tools (slide 16)

Portal walkthrough — *"From Azure Foundry, show the types of tools available."*
No code; orient the audience in the tool catalog before the code demos.

## Steps
1. Open the Foundry portal (`https://ai.azure.com`) and select your project
   (`agentic-demos`, created by `infra/provision.sh`).
2. Go to **Build › Tools** (the Foundry Tools catalog).
3. Walk the **two categories**:
   - **Built-in tools** — ready after basic config, service-executed, no hosting:
     Web search, Code Interpreter, File Search, Azure AI Search, Azure Functions,
     Function calling, Image Generation, Browser Automation, Computer Use,
     Microsoft Fabric, SharePoint.
   - **Custom tools** — bring your own: **MCP** (preview), **OpenAPI 3.0**,
     **Agent2Agent (A2A)** (preview).
4. Point out **1,400+ MCP-enabled connectors** (SAP, Salesforce, HubSpot…) and
   that any API can be exposed as an MCP tool via API Management.
5. (Optional) Mention the **private tool catalog** (Azure API Center) for
   org-scoped tool discovery.

## Bridge to the code demos
- Built-in tool in code → see `demo6` style (`WebSearchTool`, etc.).
- **MCP** → `demo6_mcp_agent/`
- **OpenAPI** → `demo7_openapi_tool/`
- **A2A** → `demo8_a2a_agent/`

Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/concepts/tool-catalog
