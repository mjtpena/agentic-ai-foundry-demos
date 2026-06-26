# Day 1 — Architect intelligent agents with Microsoft IQ and Foundry

| # | Demo | Slide | Type | Folder / file |
|---|---|---|---|---|
| 1 | Create and deploy an agent | 56 | Copilot Studio (portal) | `demo1_copilot_studio_create_agent.md` |
| 2 | Call an agent flow from an agent | 62 | Copilot Studio (portal) | `demo2_copilot_studio_agent_flow.md` |
| 3 | **Create a prompt agent** | 84 | Foundry SDK (Python) | `demo3_prompt_agent/` |
| 4 | **Deploy your first hosted agent** | 87 | Agent Framework + azd | `demo4_hosted_agent/` |

Demos 1-2 are Microsoft Copilot Studio click-throughs (provided as runbooks).
Demos 3-4 are runnable code against the Foundry project you stood up with
`infra/provision.sh`.

```bash
# from the repo root, after provisioning + pip install -r requirements.txt
python day1/demo3_prompt_agent/prompt_agent.py
cd day1/demo4_hosted_agent && ./setup.sh
```
