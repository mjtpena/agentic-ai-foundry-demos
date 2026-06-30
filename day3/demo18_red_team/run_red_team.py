#!/usr/bin/env python3
"""
Day 3 · Demo 18 — AI Red Teaming Agent  (Module 7 · "Manage compliance & security")
===================================================================================
Foundry's **AI Red Teaming Agent** automates adversarial testing: it takes seed
attack objectives across risk categories, mutates them with PyRIT **attack
strategies** (Base64, Flip, Morse, ROT13, composed…), fires them at your target
model/agent, and grades each response — producing an **Attack Success Rate (ASR)
scorecard** you can track release over release.

This is the code companion, using `azure-ai-evaluation`'s `RedTeam`:

  • risk categories : Violence · HateUnfairness · Sexual · SelfHarm
  • attack strategies: a few EASY ones + a composed (Base64 ∘ ROT13) jailbreak
  • target           : a callback that calls your deployed model
  • output           : RedTeamResult scorecard (ASR overall + per category)

A low ASR is the goal — it's evidence your guardrails (demo 14/16) hold up under
attack. The scorecard plugs into the Control Plane Compliance pane.

Slide source:
  https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/run-scans-ai-red-teaming-agent

Prereqs:
  pip install azure-ai-evaluation[redteam] azure-identity python-dotenv openai
  az login
Env:
  AZURE_AI_PROJECT_ENDPOINT    the Foundry project (required by RedTeam)
  FOUNDRY_ACCOUNT_ENDPOINT     Azure OpenAI endpoint of the target model
  MODEL_DEPLOYMENT_NAME        target deployment (default gpt-4o)
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, DIM, RESET

TARGET_DEFAULT = "gpt-4o"
NUM_OBJECTIVES = 2  # seed objectives per risk category — keep small for a live run


def _build_target(endpoint: str, deployment: str, credential):
    """A callback target: RedTeam sends an attack prompt, we return the model's reply."""
    from openai import AzureOpenAI
    from azure.identity import get_bearer_token_provider

    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default")
    client = AzureOpenAI(azure_endpoint=endpoint, azure_ad_token_provider=token_provider,
                         api_version="2024-10-21")

    def target(query: str) -> str:
        resp = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "user", "content": query}],
            max_tokens=400,
        )
        return resp.choices[0].message.content or ""

    return target


async def main() -> None:
    load_env()
    banner("Day 3 · Demo 18 — AI Red Teaming Agent",
           "azure-ai-evaluation · PyRIT attack strategies · ASR scorecard")
    project_endpoint = env("AZURE_AI_PROJECT_ENDPOINT", "PROJECT_ENDPOINT", required=True)
    model_endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT", "AZURE_OPENAI_ENDPOINT", required=True)
    deployment = env("MODEL_DEPLOYMENT_NAME", default=TARGET_DEFAULT)

    try:
        from azure.identity import DefaultAzureCredential
        from azure.ai.evaluation.red_team import RedTeam, RiskCategory, AttackStrategy
    except ImportError:
        rule("azure-ai-evaluation red-team extra not installed.", "error")
        print(f"{DIM}   pip install azure-ai-evaluation[redteam]{RESET}")
        return

    credential = DefaultAzureCredential()

    red_team = RedTeam(
        azure_ai_project=project_endpoint,
        credential=credential,
        risk_categories=[
            RiskCategory.Violence,
            RiskCategory.HateUnfairness,
            RiskCategory.Sexual,
            RiskCategory.SelfHarm,
        ],
        num_objectives=NUM_OBJECTIVES,
    )

    rule(f"Scanning target '{deployment}' — {NUM_OBJECTIVES} objectives × 4 categories", "step")
    target = _build_target(model_endpoint, deployment, credential)

    result = await red_team.scan(
        target=target,
        scan_name="accelerate-agentic-ai-demo18",
        attack_strategies=[
            AttackStrategy.Baseline,
            AttackStrategy.Base64,
            AttackStrategy.ROT13,
            AttackStrategy.Flip,
            # composed: layer two transforms for a harder jailbreak
            AttackStrategy.Compose([AttackStrategy.Base64, AttackStrategy.ROT13]),
        ],
    )

    rule("Scan complete — Attack Success Rate scorecard:", "info")
    scorecard = getattr(result, "scorecard", None) or {}
    print(f"{DIM}{scorecard}{RESET}")
    rule("Lower ASR = stronger guardrails. Track this release over release.", "ok")
    rule("Next: review the scorecard in the Control Plane Compliance pane.", "info")


if __name__ == "__main__":
    asyncio.run(main())
