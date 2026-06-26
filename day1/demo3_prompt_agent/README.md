# Day 1 · Demo 3 — Create a prompt agent

**Slide 84.** A **prompt agent** is declaratively defined — model + instructions +
tools — and Foundry hosts/orchestrates it. This is the fastest way to a working
Foundry agent.

```bash
pip install "azure-ai-projects>=2.0.0"     # Foundry projects (new) API
az login
python prompt_agent.py            # scripted France demo (exact slide script)
python prompt_agent.py --chat     # interactive multi-turn chat
python prompt_agent.py --cleanup  # delete just this agent's versions
```

**What it demonstrates beyond the slide:** the France question + capital-city
follow-up run on a *single reused conversation*, so the second answer can only be
correct if the agent used history — a concrete proof of multi-turn memory. Token
usage prints per turn.

Model: `PROMPT_AGENT_MODEL` (default `gpt-5-mini`, falls back to `gpt-4o`).
Reference: https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent
