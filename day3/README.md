# Day 3 — Trust, Security, and Control for Enterprise AI Agents

| # | Demo | Slide | Type | Folder / file |
|---|---|---|---|---|
| 13 | Foundry Control Plane capabilities | 16 | Portal | `demo13_control_plane.md` |
| 14 | **Create a Guardrail policy** | 23 | `az policy` + Portal | `demo14_guardrail_policy/` |
| 15 | View and fix compliance violations | 26 | Portal (+ CLI check) | `demo15_fix_compliance_violations.md` |
| 16 | **Configure guardrails & controls** | 49 | Python + Portal | `demo16_guardrails_content_safety/` |

Suggested order: **13** (tour the Control Plane) → **14** (create a policy in
Audit mode) → **15** (find & fix violations) → **16** (configure + test guardrails).

```bash
# from repo root, after provisioning + pip install -r requirements.txt
day3/demo14_guardrail_policy/create_guardrail_policy.sh
python day3/demo16_guardrails_content_safety/configure_content_safety.py
python day3/demo16_guardrails_content_safety/test_guardrails.py
```
