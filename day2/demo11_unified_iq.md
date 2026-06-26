# Day 2 · Demo 11 — Build unified agents using Work IQ, Fabric IQ, and Foundry IQ (slide 69)

The capstone integration. Per the slide notes, the flow is:

> Create a Fabric Data Agent → integrate the Fabric IQ Ontology → create a
> Foundry agent with Foundry IQ configured → add the Fabric Data Agent as a tool
> → add Work IQ (Mail or Teams) as an MCP tool. The agent now has all 3 IQs and
> can answer questions across business context, data, and organizational context.

This spans Fabric + Foundry + Microsoft 365, so it's a guided runbook. The
reusable code building blocks already exist in this repo.

## Prerequisites
- Microsoft Fabric workspace with data + an **Ontology** (Fabric IQ).
- A Microsoft 365 Copilot license (for Work IQ MCP — Mail/Teams).
- The Foundry project from `infra/provision.sh`.

## Steps
1. **Fabric Data Agent** — in Fabric, create a Data Agent over your lakehouse/
   warehouse; attach the **Fabric IQ Ontology** so it reasons over entities
   (Store, Product, Freezer) and relationships, not raw tables.
   Test: *"For each store, show any freezers that ever had humidity < 46%."*
2. **Foundry IQ knowledge** — ground a Foundry agent with an Azure AI Search
   knowledge base. You already built one in **demo 9/10**
   (`earth-at-night-kb`) — reuse that pattern with your own index.
3. **Add the Fabric Data Agent as a tool** to the Foundry agent (Foundry Tools
   › add the Fabric/A2A connection). The A2A wiring is in **demo 8**.
4. **Add Work IQ as an MCP tool** — add the **Work IQ Mail** (or Teams) MCP
   server to the agent (Foundry Tools › MCP). The MCP wiring is in **demo 6**.
5. **Result** — one agent that answers across:
   - **Work IQ** — your mail/Teams/org context,
   - **Fabric IQ** — your governed business data via the Ontology,
   - **Foundry IQ** — your unstructured knowledge via agentic retrieval.

## Demo prompts
- *"Summarize the freezer humidity issues per store and email the facilities lead a recap."* (Fabric IQ + Work IQ)
- *"Which product drove the most revenue, and what do our docs say about its handling?"* (Fabric IQ + Foundry IQ)

References:
- Fabric Data Agent + Ontology: https://learn.microsoft.com/en-us/fabric/iq/Ontology/tutorial-4-create-data-agent
- Work IQ MCP: https://learn.microsoft.com/en-us/microsoft-copilot-studio/use-work-iq
