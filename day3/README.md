# Day 3 — Trust, Security, and Control for Enterprise AI Agents

| # | Demo | Slide | Type | Folder / file |
|---|---|---|---|---|
| 13 | Foundry Control Plane capabilities | 16 | Portal | `demo13_control_plane.md` |
| 14 | **Create a Guardrail policy** | 23 | `az policy` + Portal | `demo14_guardrail_policy/` |
| 15 | View and fix compliance violations | 26 | Portal (+ CLI check) | `demo15_fix_compliance_violations.md` |
| 16 | **Configure guardrails & controls** | 49 | Python + Portal | `demo16_guardrails_content_safety/` |
| 17 | **Evaluate, monitor & optimize agents** | 40 | Python + UI | `demo17_evaluations/` |
| 18 | **AI Red Teaming Agent** | 41 | Python + UI | `demo18_red_team/` |
| 19 | **Agent observability (OpenTelemetry)** | 16 | Python + UI | `demo19_observability/` |
| 20 | **Secure agents with Entra Agent ID** | 45 | Python + CLI + Portal | `demo20_entra_agent_id/` |
| 20b | Agent 365 (IT admin control plane) | — | Portal (Module 8) | `demo20_entra_agent_id/agent365_runbook.md` |
| 21 | **Advanced Guardrails** (XPIA · protected material · PII) | 49 | Python + UI + Portal | `demo21_advanced_guardrails/` |
| 22 | **Purview & DLP for AI agents** | 26 | Portal | `demo22_purview_dlp/` |

Suggested order: **13** (tour the Control Plane) → **14** (create a policy in
Audit mode) → **15** (find & fix violations) → **16** (configure + test guardrails)
→ **17** (evaluate quality + safety) → **18** (red-team the model) → **19** (trace
it with observability) → **20** (secure it with Entra + govern the fleet with
Agent 365). 13–16 + 20/20b map to Module 7/8 governance; 17–19 map to the
"evaluate, monitor and optimize" + "observability" bullets.

```bash
# from repo root, after provisioning + pip install -r requirements.txt
day3/demo14_guardrail_policy/create_guardrail_policy.sh
python day3/demo16_guardrails_content_safety/configure_content_safety.py
python day3/demo16_guardrails_content_safety/test_guardrails.py
python day3/demo17_evaluations/evaluate_agent.py
python day3/demo18_red_team/run_red_team.py            # needs azure-ai-evaluation[redteam]
python day3/demo19_observability/trace_agent.py
python day3/demo20_entra_agent_id/inspect_identity.py
python day3/demo21_advanced_guardrails/advanced_guardrails.py
```

> Demos 17–20 also run in the live console (`ui/`) with always-installed
> dependencies — click-to-run, no preview packages needed. View Source in the
> console shows these real Foundry-SDK scripts.
