# Foundry Live Demo Console — container image for Azure Container Apps.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first (cached layer), pinned to versions verified locally.
# Install top-level, UI, and hosted-agent deps so the hosted agent can run in-process.
COPY requirements.txt /tmp/requirements.txt
COPY ui/requirements-deploy.txt /tmp/requirements-deploy.txt
COPY day1/demo4_hosted_agent/requirements.txt /tmp/hosted-requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements-deploy.txt -r /tmp/hosted-requirements.txt

# App code (.dockerignore excludes .venv / .env / .git / etc.)
COPY . /app

EXPOSE 8000
# Start the hosted-agent in the background (if present) and then start the UI server.
CMD ["sh", "-c", "python day1/demo4_hosted_agent/agent.py & exec python -m uvicorn ui.server.main:app --host 0.0.0.0 --port 8000"]
