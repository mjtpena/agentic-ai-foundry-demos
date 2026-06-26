# Day 1 · Demo 2 — Call an agent flow from an agent (Copilot Studio)

**Slide 62.** Portal demo: give an agent the ability to return a weather forecast
by calling an **agent flow** (Power Automate). Runbook only — no `az` step.

## Prerequisite
A published **Get weather forecast** flow that takes a city + ZIP and returns
`location`, `day_summary`, `chance_of_rain`. (Create it in Power Automate first
if you haven't.)

## A) Add the flow as a tool
1. Copilot Studio › **Agents** › select your agent.
2. **Tools** › **Add a tool** › **Flow**.
3. Pick **Get weather forecast**, then **Add and configure**.
4. Give it a clear **name + description** so the orchestrator knows when to use
   it, e.g. *"Get today's weather forecast for a city name or ZIP code."*
5. Configure **Inputs** (how the agent fills each variable) and **Completion**
   behaviour, then **Save**.

## B) Call the flow from a topic
1. **Topics** › new topic **Get weather**. Trigger phrases: *will it rain*,
   *today's forecast*, *get weather*, *what's the weather*.
2. Add **Send a message**: *"I can help you with that."*
3. Add **Ask a question** → *"What is your city?"* → identify **User's entire
   response** (variable `Var1`/`City`).
4. Add another **Ask a question** → *"What is your ZIP code?"* → identify
   **Number** (`Var2`/`ZIPcode`).
5. Add **Add a tool** → the **Get weather forecast** flow. Map City←Var1,
   ZIP←Var2.
6. Add a **Message** node using the outputs:
   *"Today's forecast for `location`: `day_summary`. Chance of rain is
   `chance_of_rain`%."* → **Save**.

## C) Test
In the test pane, type a trigger phrase, answer the city/ZIP prompts, and
confirm the forecast renders.

Reference: https://learn.microsoft.com/en-us/microsoft-copilot-studio/advanced-use-flow
