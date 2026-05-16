# FastAPI Standard Example

`examples/fastapi-standard` is a production-style FastAPI starter for teams that want a small but modern baseline. It uses `uv`, Ruff, `SQLModel`, Alembic, `pydantic-settings`, an explicit service layer, and an application lifespan hook.

## Stack

- Python 3.12+
- `uv`
- FastAPI
- SQLModel
- Alembic
- `pydantic-settings`
- Ruff
- `python-dotenv`

## Project layout

```text
fastapi-standard/
├── .env.example
├── .gitignore
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── alembic.ini
├── pyproject.toml
├── ruff.toml
└── src/
    └── app/
        ├── api/
        │   └── routes/
        │       ├── health.py
        │       └── widgets.py
        ├── core/
        │   └── config.py
        ├── db/
        │   ├── models.py
        │   └── session.py
        ├── schemas/
        │   └── widget.py
        ├── services/
        │   └── widgets.py
        └── main.py
```

## Install

Create the environment and install dependencies:

```bash
uv sync
```

Copy the example environment file:

```bash
cp .env.example .env
```

## Run locally

Apply database migrations:

```bash
uv run alembic upgrade head
```

Start the development server:

```bash
uv run uvicorn app.main:app --reload
```

The service will be available at `http://127.0.0.1:8000`.

## Migrations

Create a new migration after model changes:

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

Roll back one migration:

```bash
uv run alembic downgrade -1
```

This starter already includes an initial migration for the sample `Widget` table so the structure feels realistic from day one.

## Environment variables

Settings come from `.env` through `pydantic-settings`.

Important values:

- `APP_NAME`: name shown in OpenAPI metadata
- `APP_ENV`: local, staging, or production style marker
- `APP_HOST`: host for local serving
- `APP_PORT`: port for local serving
- `API_V1_PREFIX`: API namespace prefix
- `DATABASE_URL`: SQLite by default for the example, replace with PostgreSQL in production
- `CORS_ORIGINS`: comma-separated frontend origins
- `SQL_ECHO`: SQL logging toggle for local debugging

## API example

Health check:

```bash
curl http://127.0.0.1:8000/health
```

List widgets:

```bash
curl http://127.0.0.1:8000/api/v1/widgets/
```

Create a widget:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/widgets/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Primary Widget","description":"Created from the sample API"}'
```

## Structure notes

- `app.main` builds the FastAPI app and owns middleware, router wiring, and lifespan.
- `app.core.config` centralizes environment-driven settings.
- `app.db` owns database connectivity and model declarations.
- `app.schemas` exposes request and response contracts.
- `app.services` keeps business logic out of the route layer.

## Development workflow

Use `uv` for every local task:

```bash
uv run ruff check .
uv run ruff format .
uv run alembic current
```

Recommended branch model:

- `main`: always releasable
- `development`: optional integration branch for teams that want a shared staging lane
- `feature/<name>`: short-lived branches merged through pull requests after review

That keeps the repo aligned with GitHub Flow while still supporting a `development` branch when teams want one.
