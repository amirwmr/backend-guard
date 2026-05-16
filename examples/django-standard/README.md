# Django Standard Example

`examples/django-standard` is a production-style Django starter meant to be inspected, copied, and adapted. It stays intentionally small, but it uses the same habits you would want in a serious backend service: `uv` for package management, Ruff for linting, split settings, environment-driven configuration, DRF, a health endpoint, and a structure that scales.

## Stack

- Python 3.12+
- `uv`
- Django
- Django REST Framework
- Django ORM
- `django-environ`
- Ruff
- WhiteNoise
- optional JWT support through `djangorestframework-simplejwt`

## Project layout

```text
django-standard/
├── .env.example
├── .gitignore
├── manage.py
├── pyproject.toml
├── ruff.toml
└── src/
    ├── apps/
    │   └── core/
    │       ├── admin.py
    │       ├── apps.py
    │       ├── migrations/
    │       ├── models.py
    │       ├── serializers.py
    │       ├── urls.py
    │       └── views.py
    └── config/
        ├── asgi.py
        ├── settings/
        │   ├── base.py
        │   ├── dev.py
        │   └── prod.py
        ├── urls.py
        └── wsgi.py
```

## Install

Create the environment and install dependencies:

```bash
uv sync
```

If you want optional JWT support as well:

```bash
uv sync --extra jwt
```

Copy the environment template:

```bash
cp .env.example .env
```

## Run locally

Apply migrations:

```bash
uv run python manage.py migrate
```

Create an admin account:

```bash
uv run python manage.py createsuperuser
```

Start the development server:

```bash
uv run python manage.py runserver
```

## Migrations

Generate new migrations after model changes:

```bash
uv run python manage.py makemigrations
```

Apply them:

```bash
uv run python manage.py migrate
```

This example already includes an initial migration for the sample `Widget` model so the starter can be inspected with a realistic baseline.

## Environment variables

Configuration is loaded from `.env` through `django-environ`.

Important values:

- `DJANGO_SETTINGS_MODULE`: defaults to `config.settings.dev` through `manage.py`
- `DJANGO_SECRET_KEY`: required in every environment
- `DJANGO_DEBUG`: set to `true` for local development only
- `DJANGO_ALLOWED_HOSTS`: comma-separated hostnames
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated trusted origins
- `DATABASE_URL`: SQLite by default for local work, replace with PostgreSQL or another production database in real deployments

## Superuser workflow

Create the first admin user with:

```bash
uv run python manage.py createsuperuser
```

Then open `/admin/` and sign in with that account.

## API example

Health check:

```bash
curl http://127.0.0.1:8000/health/
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

## Development workflow

Use `uv` for all local commands:

```bash
uv run ruff check .
uv run ruff format .
uv run python manage.py check --deploy
```

Recommended branch model:

- `main`: production-ready history only
- `development`: optional shared integration branch for teams that want one extra stabilization lane
- `feature/<name>`: short-lived branches opened from `main` or `development`, merged back through pull requests

That keeps the repo close to GitHub Flow while leaving room for teams that prefer a `development` branch during active product work.
