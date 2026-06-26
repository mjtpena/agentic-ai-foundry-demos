# Day 3 · Demo 16 — Configure guardrails & controls (portal version, slide 49)

The Guardrails wizard in Foundry. The Python scripts here exercise the same
Content Safety engine in code.

## Create a guardrail
1. Foundry → your project → **Build** (top-right).
2. Left nav → **Guardrails** → **Create Guardrail** (opens Step 1: Add Controls).

## Add controls
- Pick a **risk** from the dropdown (Violence, Hate, Sexual, Self-harm, Protected
  material, Ungrounded attributes, Prompt injection — direct/indirect, Task adherence).
- Choose **intervention points** (user input / model output) and an **action**
  (e.g. *Annotate and block*). Some risks are valid only at certain points.
- **Add control**. Repeat. (Violence/Hate/Sexual/Self-harm on inputs/outputs can
  only be *overridden*, not deleted.)

## Assign + name
3. **Next** → assign the guardrail to **agents and/or models** in the project → **Save**.
4. **Next** → **Review** → name it → **Create**.

## Test (matches `test_guardrails.py`)
- Select the guardrail → **Try in Playground** (assign it to a non-prod model/agent first).
- Send queries; when an "Annotate and block" control trips, the chat shows which
  risk was detected and at which intervention point.

> Defaults: content filters sit at a **medium** threshold and are adjustable by
> severity — exactly the `--threshold` dial in `test_guardrails.py`.

Reference: https://learn.microsoft.com/en-us/azure/foundry/guardrails/how-to-create-guardrails
