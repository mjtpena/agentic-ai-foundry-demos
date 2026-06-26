#!/usr/bin/env python3
"""
Day 2 · Demo 6 — Connect MCP tools to agents  (slide 27)
========================================================
Builds an agent that connects to a cloud-hosted **MCP server** — the public
**Microsoft Learn Docs** MCP server (`https://learn.microsoft.com/api/mcp`) — so
it can answer developer questions from Microsoft's latest official docs.

This assembles every code block the slide walks through (Add references →
Connect → Initialize MCP tool → Create agent → thread → message → set approval
→ run → display steps), into one runnable file, then adds: argument-driven
prompts, a clean tool-call trace, and guaranteed agent cleanup.

Slide / lab source:
  https://microsoftlearning.github.io/mslearn-ai-agents/Instructions/03c-use-agent-tools-with-mcp.html

Prereqs:
  pip install azure-ai-projects azure-ai-agents mcp azure-identity
  az login
Env (from .env): PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME, MCP_SERVER_URL, MCP_SERVER_LABEL
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, agent_says, DIM, RESET

# --- Add references (slide) -------------------------------------------------
from azure.identity import DefaultAzureCredential
from azure.ai.agents import AgentsClient
try:
    # McpTool ships in the PRERELEASE azure-ai-agents (see the lab's `pip install --pre`).
    from azure.ai.agents.models import McpTool, ToolSet, ListSortOrder
except ImportError as _e:
    raise SystemExit(
        "This demo needs the prerelease azure-ai-agents (McpTool). Install with:\n"
        "  pip install --pre azure-ai-projects azure-ai-agents mcp\n"
        f"(import error: {_e})"
    )

DEFAULT_PROMPT = "Give me the Azure CLI commands to create an Azure Container App with a managed identity."


def run(prompt: str) -> None:
    project_endpoint = env("PROJECT_ENDPOINT", "FOUNDRY_PROJECT_ENDPOINT", required=True)
    model_deployment = env("MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    mcp_server_url = env("MCP_SERVER_URL", default="https://learn.microsoft.com/api/mcp")
    mcp_server_label = env("MCP_SERVER_LABEL", default="mslearn")

    # --- Connect to the agents client (slide) -------------------------------
    agents_client = AgentsClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(
            exclude_environment_credential=True,
            exclude_managed_identity_credential=True,
        ),
    )

    with agents_client:
        # --- Initialize agent MCP tool (slide) ------------------------------
        rule(f"MCP server: {mcp_server_label} @ {mcp_server_url}", "step")
        mcp_tool = McpTool(server_label=mcp_server_label, server_url=mcp_server_url)
        mcp_tool.set_approval_mode("never")  # auto-invoke tools, no human approval
        toolset = ToolSet()
        toolset.add(mcp_tool)

        # --- Create a new agent (slide) -------------------------------------
        agent = agents_client.create_agent(
            model=model_deployment,
            name="my-mcp-agent",
            instructions=(
                "You have access to an MCP server called `microsoft.docs.mcp` - "
                "this tool allows you to search through Microsoft's latest official "
                "documentation. Use the available MCP tools to answer questions and "
                "perform tasks."
            ),
        )
        rule(f"Created agent, ID: {agent.id}", "ok")

        # --- Create thread + message (slide) --------------------------------
        thread = agents_client.threads.create()
        rule(f"Created thread, ID: {thread.id}", "info")
        message = agents_client.messages.create(thread_id=thread.id, role="user", content=prompt)
        user_says(prompt)
        rule(f"Created message, ID: {message.id}", "info")

        # --- Create and process run with MCP tools (slide) ------------------
        mcp_tool.set_approval_mode("never")
        run_obj = agents_client.runs.create_and_process(
            thread_id=thread.id, agent_id=agent.id, toolset=toolset
        )
        rule(f"Run finished with status: {run_obj.status}", "ok" if str(run_obj.status).endswith("COMPLETED") else "warn")
        if run_obj.last_error:
            rule(f"Run error: {run_obj.last_error}", "error")

        # --- Display run steps and tool calls (slide) -----------------------
        print(f"\n{DIM}--- MCP tool calls ---{RESET}")
        for step in agents_client.run_steps.list(thread_id=thread.id, run_id=run_obj.id):
            details = step.get("step_details", {})
            tool_calls = details.get("tool_calls", [])
            for call in tool_calls:
                print(f"   Tool Call ID: {call.get('id')}")
                print(f"   Type: {call.get('type')}")
                fn = call.get("name") or call.get("function", {}).get("name")
                if fn:
                    print(f"   Tool: {fn}")

        # --- Print the conversation -----------------------------------------
        print(f"\n{DIM}--- Conversation ---{RESET}")
        messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for m in messages:
            if m.text_messages:
                text = m.text_messages[-1].text.value
                (agent_says if m.role == "assistant" else user_says)(text)

        # --- Clean up the agent (slide) -------------------------------------
        agents_client.delete_agent(agent.id)
        rule("Deleted agent", "ok")


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP tools agent (Day 2 #6)")
    parser.add_argument("prompt", nargs="?", default=DEFAULT_PROMPT,
                        help="developer question to answer from Microsoft docs")
    args = parser.parse_args()
    load_env()
    banner("Day 2 · Demo 6 — Connect MCP tools to agents",
            "azure-ai-agents · Microsoft Learn Docs MCP server · auto tool-use")
    run(args.prompt)
    print()
    rule("Re-run with your own question, e.g.:  python client.py \"How do I deploy a Foundry hosted agent?\"", "info")


if __name__ == "__main__":
    main()
