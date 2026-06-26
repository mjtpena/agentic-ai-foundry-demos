# Day 2 · Demo 7 — Connect to an OpenAPI Specification (slide 30)

A Foundry agent with an **OpenAPI 3.0 tool** that calls the live wttr.in weather
API (anonymous auth) from the spec in `assets/weather_openapi.json`.

```bash
pip install azure-ai-projects jsonref python-dotenv azure-identity
az login
python openapi_agent.py            # "What's the weather in Seattle?"
python openapi_agent.py London
```
The file keeps the slide's key-based and managed-identity auth variants as
reference (`_reference_auth_variants`), runs the slide's environment pre-flight,
and deletes the agent version on exit.

`assets/weather_openapi.json` is a complete, valid OpenAPI 3.0 spec with an
`operationId` (`getWeather`) — the one hard requirement the slide calls out.

Env: `AZURE_AI_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`.
Reference: https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/openapi
