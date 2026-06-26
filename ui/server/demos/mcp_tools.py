"""Day 2 · Demo 6 — Connect MCP tools to agents (slide 27)."""
from __future__ import annotations

from ..foundry import env
from ..sse import EventStream

DEFAULT_PROMPT = (
    "Give me the Azure CLI commands to create an Azure Container App with a managed identity."
)
INSTRUCTIONS = (
    "You have access to an MCP server called `microsoft.docs.mcp` - this tool "
    "allows you to search through Microsoft's latest official documentation. Use "
    "the available MCP tools to answer questions and perform tasks."
)


def run(stream: EventStream, payload: dict) -> None:
    from azure.identity import DefaultAzureCredential
    from azure.ai.agents import AgentsClient
    from azure.ai.agents.models import McpTool, ToolSet, ListSortOrder

    endpoint = env("PROJECT_ENDPOINT", "FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        stream.error("PROJECT_ENDPOINT is not set — run infra/provision first.")
        return
    model = env("MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    url = env("MCP_SERVER_URL", default="https://learn.microsoft.com/api/mcp")
    label = env("MCP_SERVER_LABEL", default="mslearn")
    prompt = (payload or {}).get("prompt") or DEFAULT_PROMPT

    credential = DefaultAzureCredential(
        exclude_environment_credential=True,
        exclude_managed_identity_credential=True,
    )
    client = AgentsClient(endpoint=endpoint, credential=credential)
    with client:
        stream.foundry("MCP server", f"{label} @ {url}", kind="mcp")
        mcp_tool = McpTool(server_label=label, server_url=url)
        mcp_tool.set_approval_mode("never")
        toolset = ToolSet()
        toolset.add(mcp_tool)

        stream.status(f"Creating agent on {model} with the MCP tool", kind="step")
        agent = client.create_agent(model=model, name="my-mcp-agent", instructions=INSTRUCTIONS)
        stream.foundry("Agent", agent.id, kind="agent", model=model)

        thread = client.threads.create()
        stream.foundry("Thread", thread.id, kind="thread")
        client.messages.create(thread_id=thread.id, role="user", content=prompt)
        stream.user(prompt)

        stream.status("Running — the agent decides which docs tools to call…", kind="step")
        run_obj = client.runs.create_and_process(
            thread_id=thread.id, agent_id=agent.id, toolset=toolset
        )
        status = str(run_obj.status)
        stream.foundry("Run status", status, kind="run" if status.upper().endswith("COMPLETED") else "warn")
        if run_obj.last_error:
            stream.error(str(run_obj.last_error))

        n_calls = 0
        for step in client.run_steps.list(thread_id=thread.id, run_id=run_obj.id):
            details = step.get("step_details", {}) if hasattr(step, "get") else {}
            for call in details.get("tool_calls", []):
                n_calls += 1
                fn = call.get("name") or call.get("function", {}).get("name") or call.get("type")
                stream.foundry("MCP tool call", fn, kind="toolcall", id=call.get("id"))
        stream.metric("MCP tool calls", n_calls)

        messages = client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for m in messages:
            if m.role == "assistant" and m.text_messages:
                stream.answer(m.text_messages[-1].text.value)

        client.delete_agent(agent.id)
        stream.status("Agent cleaned up", kind="ok")
