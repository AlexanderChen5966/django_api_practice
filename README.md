# Weather API Practice

Domain-driven Django API that aggregates weather forecasts from OpenWeatherMap (OWM) and Taiwan CWA.

## Getting Started

1. Create a virtualenv and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r web_api_practice/requirements.txt
   ```
2. Copy the example environment file and fill in your keys:
   ```bash
   cp web_api_practice/.env.example web_api_practice/.env
   ```
   Required variables:
   - `OWM_API_KEY`: OpenWeatherMap API key.
   - `CWA_API_KEY`: CWA OpenData API key.
   - `HTTP_DEFAULT_TIMEOUT`, `HTTP_MAX_RETRIES`: optional tuning knobs.
3. Run migrations and start the dev server:
   ```bash
   python web_api_practice/manage.py migrate
   python web_api_practice/manage.py runserver
   ```

## API

- `GET /api/v1/providers` — list available upstream providers and required query params.
- `GET /api/v1/weather/forecast` — fetch a normalized forecast. Supply either `city` + `country` (OWM) or `locationName` (CWA). The service automatically caches responses, applies provider fallbacks, and exposes consistent periods.

Swagger UI lives at `GET /api/docs/` (powered by drf-spectacular).

## Testing

Automated tests cover adapters, service fallbacks, and HTTP views.

```bash
cd web_api_practice
pytest -q
```

For framework sanity checks:

```bash
python manage.py check
```

## Logging and Operations

- Enable structured logging by defining Django LOGGING settings. Recommended minimal config:
  - Attach a `logging.StreamHandler` at INFO for `apps.weather` to trace upstream calls and fallbacks.
  - Emit warning/error level logs when providers fail so alerting can key off them.
- Consider surfacing cache hit/miss metrics (e.g., via Prometheus or OpenTelemetry) to observe provider stability.
- When deploying, set reasonable timeout/retry values via environment variables and monitor them with APM tools.
- Schedule periodic smoke tests (cron or external monitor) to call `/api/v1/weather/forecast` using both providers to ensure credentials remain valid.
