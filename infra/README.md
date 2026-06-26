# Infrastructure — provision everything with your Azure CLI

One script stands up every Azure resource the code demos need, then writes a
populated `../.env` that the Python demos read. **Run this on a machine where
you've signed in with `az login`** — it uses *your* subscription.

## What gets created

| Resource | Name (default) | Used by |
|---|---|---|
| Resource group | `rg-agentic-ai-demos` | everything |
| Microsoft Foundry account (`AIServices`) + project | `foundry-aa-<suffix>` / `agentic-demos` | Day 1 & 2 SDK demos |
| Model: `gpt-4o` | universal fallback | most demos |
| Model: `gpt-4.1`, `gpt-4.1-mini` | hosted agent, tools | Day 1 #4, Day 2 |
| Model: `gpt-5-mini` | prompt agent | Day 1 #3 |
| Model: `text-embedding-3-large` | vectorizer | Day 2 #9/#10 |
| Azure AI Search (`basic`) | `srch-aa-<suffix>` | Day 2 #9/#10 |
| Storage + container | `staa<suffix>` / `earth-at-night-data` | Day 2 #9/#10 |
| RBAC role assignments | — | DefaultAzureCredential auth |

## Run it

```bash
az login
az account set -s "<your-subscription>"        # if you have more than one
cd infra
./provision.sh                                  # bash / macOS / Linux / WSL / Cloud Shell
#   ...or on Windows PowerShell:
./provision.ps1
```

Then load the Day 2 retrieval sample data:

```bash
./upload_sample_data.sh
```

Everything is **idempotent** — re-run any time. Names are overridable with env
vars before you call the script, e.g. `LOCATION=swedencentral SUFFIX=mj01 ./provision.sh`.

## A note on Australia East + the newest models

`gpt-5-mini` and `gpt-4.1` roll out region-by-region. If a deployment can't be
created in `australiaeast`, the script prints a clear warning and keeps going —
**`gpt-4o` always deploys**, and every demo falls back to it via the
`MODEL_DEPLOYMENT_NAME` in `.env`. To use the newer models, either set
`LOCATION` to a region that offers them and re-run, or change the deployment
names in `.env` once they're available.

## The one piece that can need a portal click

The Foundry **project** sub-resource is created through the Azure management
REST API (`PROJECTS_API_VERSION` in `00-variables.sh`). Microsoft bumps that
api-version periodically. If creation fails, the script tells you exactly what
to do: open the Foundry portal, create a project named `agentic-demos`, copy its
endpoint, and paste it into `../.env` as `PROJECT_ENDPOINT`. Everything else is
already wired.

## Clean up (stop charges)

```bash
./teardown.sh        # or ./teardown.ps1 — deletes the whole resource group
```
