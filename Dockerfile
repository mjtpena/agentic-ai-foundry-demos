# Foundry Live Demo Console — container image for Azure Container Apps.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first (cached layer), pinned to versions verified locally.
COPY ui/requirements-deploy.txt /tmp/requirements-deploy.txt
RUN pip install --no-cache-dir -r /tmp/requirements-deploy.txt

# App code (.dockerignore excludes .venv / .env / .git / etc.)
COPY . /app

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "ui.server.main:app", "--host", "0.0.0.0", "--port", "8000"]
