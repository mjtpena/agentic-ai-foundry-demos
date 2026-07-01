# Contributing

Thanks for contributing to Accelerate Agentic AI demos.

## Development setup

1. Create a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
   - `pip install -r ui/requirements-ui.txt`
3. Copy `.env.example` to `.env` and configure your own endpoints.
4. Run the UI with `.\ui\run.ps1` (Windows) or `./ui/run.sh` (bash).

## Contribution guidelines

- Keep changes focused and demo-safe.
- Preserve environment-driven configuration (no hardcoded secrets or tenant-specific values).
- Update docs when behavior/configuration changes.
- Validate changes locally before opening a PR.

## Pull requests

- Provide a clear summary of the change and affected demos.
- Include setup notes if reviewers need specific env vars or resources.
