# Day 2 · Demo 12 — Create and run an agent with Agent Framework (slide 83)

```bash
pip install agent-framework azure-identity python-dotenv
az login
python joker_agent.py                 # run() + run_stream() + multimodal (slide)
python joker_agent.py --image ""       # skip the image turn
python weather_agent_with_tools.py     # BEYOND: ai_function tools + AgentThread memory
```

- `joker_agent.py` — the slide's "Joker" agent, shown all three ways: single
  `run()`, streaming `run_stream()`, and a multimodal `ChatMessage` (text+image).
- `weather_agent_with_tools.py` — the next step the framework slides describe:
  Python functions wrapped as `@ai_function` tools, with a persistent
  `AgentThread` so memory + tool-use carry across turns.

Auth: `AzureCliCredential` (`az login`), per the slide prerequisites.
Env: `FOUNDRY_ACCOUNT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME`.
Reference: https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent
