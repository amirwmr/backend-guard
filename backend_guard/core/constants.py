"""Project-wide constants."""

from __future__ import annotations

TOOL_NAME = "backend-guard"
CONFIG_FILE_NAME = ".backend-guard.toml"
INSTALL_MANIFEST_NAME = "install-manifest.json"
STATE_DIR_NAME = ".backend-guard"
MANAGED_MARKER = "managed-by-backend-guard"
MIN_PYTHON_VERSION = (3, 12)

DEFAULT_TIMEOUT_SECONDS = 900

DEFAULT_DEV_PACKAGES = [
    "pre-commit",
    "ruff",
    "bandit",
    "detect-secrets",
    "pip-audit",
    "pyupgrade",
]

PRE_COMMIT_HOOK_REPOS = {
    "pre-commit-hooks": "v5.0.0",
    "astral-sh/ruff-pre-commit": "v0.6.9",
    "asottile/pyupgrade": "v3.17.0",
    "PyCQA/bandit": "1.7.10",
    "Yelp/detect-secrets": "v1.5.0",
    "pypa/pip-audit": "v2.7.3",
}

MANAGED_FILES = {
    ".pre-commit-config.yaml",
    "ruff.toml",
    ".editorconfig",
    ".env.example",
    ".backend-guard.toml",
    ".github/workflows/backend-guard.yml",
}

MANAGED_BLOCK_FILES = {
    ".gitignore",
    "Makefile",
}

FASTAPI_KEYWORDS = {
    "fastapi",
    "starlette",
    "uvicorn",
    "pydantic-settings",
}

DJANGO_KEYWORDS = {
    "django",
    "djangorestframework",
    "gunicorn",
    "whitenoise",
}

GENERIC_BACKEND_KEYWORDS = {
    "sqlalchemy",
    "alembic",
    "celery",
    "redis",
    "psycopg",
    "gunicorn",
    "uvicorn",
}

SKIP_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "node_modules",
}
