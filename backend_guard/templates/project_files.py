"""Project file templates."""

from __future__ import annotations

from pathlib import Path

from backend_guard.core.config import BackendGuardConfig
from backend_guard.core.constants import PRE_COMMIT_HOOK_REPOS
from backend_guard.core.models import ProjectAnalysis, ProjectKind


def render_pre_commit_config(project: ProjectAnalysis, config: BackendGuardConfig) -> str:
    """Render a secure default pre-commit configuration."""
    bandit_args = (
        "        args: [-c, pyproject.toml, -r, .]"
        if project.pyproject_path
        else "        args: [-r, .]"
    )
    repositories = [
        f"""repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: {PRE_COMMIT_HOOK_REPOS["pre-commit-hooks"]}
    hooks:
      - id: check-added-large-files
      - id: check-json
      - id: check-merge-conflict
      - id: check-toml
      - id: check-yaml
      - id: debug-statements
      - id: end-of-file-fixer
      - id: mixed-line-ending
      - id: trailing-whitespace""",
        f"""  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: {PRE_COMMIT_HOOK_REPOS["astral-sh/ruff-pre-commit"]}
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format""",
        f"""  - repo: https://github.com/asottile/pyupgrade
    rev: {PRE_COMMIT_HOOK_REPOS["asottile/pyupgrade"]}
    hooks:
      - id: pyupgrade
        args: [--py312-plus]""",
        f"""  - repo: https://github.com/PyCQA/bandit
    rev: {PRE_COMMIT_HOOK_REPOS["PyCQA/bandit"]}
    hooks:
      - id: bandit
{bandit_args}
        exclude: ^tests/""",
        f"""  - repo: https://github.com/Yelp/detect-secrets
    rev: {PRE_COMMIT_HOOK_REPOS["Yelp/detect-secrets"]}
    hooks:
      - id: detect-secrets
        args: [--exclude-files, '(?x)^(.*/tests/fixtures/|.*/.venv/|.*/venv/)']""",
        f"""  - repo: https://github.com/pypa/pip-audit
    rev: {PRE_COMMIT_HOOK_REPOS["pypa/pip-audit"]}
    hooks:
      - id: pip-audit
        args: [--progress-spinner=off]""",
    ]

    if config.tools.include_black:
        repositories.append(
            """  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black"""
        )

    if config.tools.include_isort:
        repositories.append(
            """  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort"""
        )

    if config.tools.include_git_secrets:
        repositories.append(
            """  - repo: local
    hooks:
      - id: git-secrets
        name: git-secrets
        entry: git secrets --scan
        language: system
        pass_filenames: false"""
        )

    if config.tools.include_osv_scanner:
        repositories.append(
            """  - repo: local
    hooks:
      - id: osv-scanner
        name: osv-scanner
        entry: osv-scanner scan --lockfile=uv.lock
        language: system
        pass_filenames: false"""
        )

    if config.tools.include_safety:
        repositories.append(
            """  - repo: local
    hooks:
      - id: safety
        name: safety
        entry: safety check --full-report
        language: system
        pass_filenames: false"""
        )

    if project.kind is ProjectKind.DJANGO:
        repositories.append(
            """  - repo: local
    hooks:
      - id: django-deploy-check
        name: django deploy checks
        entry: python manage.py check --deploy
        language: system
        pass_filenames: false"""
        )

    return "\n".join(repositories)


def render_ruff_toml(project: ProjectAnalysis) -> str:
    """Render a strict Ruff configuration."""
    framework_specific = ""
    if project.kind is ProjectKind.DJANGO:
        framework_specific = (
            '\n[lint.per-file-ignores]\n"**/migrations/*.py" = ["E501", "RUF012"]\n'
        )

    return f"""target-version = "py312"
line-length = 100
src = ["."]

[lint]
select = ["E", "F", "I", "UP", "B", "C4", "SIM", "RUF"]
ignore = ["B008"]

[format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
{framework_specific}"""


def render_backend_guard_config(config: BackendGuardConfig) -> str:
    """Render the default backend-guard configuration file."""
    return f"""version = {config.version}

[files]
editorconfig = {str(config.files.editorconfig).lower()}
env_example = {str(config.files.env_example).lower()}
gitignore = {str(config.files.gitignore).lower()}
makefile = {str(config.files.makefile).lower()}
github_actions = {str(config.files.github_actions).lower()}

[checks]
lint = {str(config.checks.lint).lower()}
format = {str(config.checks.format).lower()}
security = {str(config.checks.security).lower()}
dependencies = {str(config.checks.dependencies).lower()}
secrets = {str(config.checks.secrets).lower()}  # pragma: allowlist secret
git = {str(config.checks.git).lower()}
framework = {str(config.checks.framework).lower()}
doctor = {str(config.checks.doctor).lower()}

[tools]
use_ruff_format = {str(config.tools.use_ruff_format).lower()}
include_black = {str(config.tools.include_black).lower()}
include_isort = {str(config.tools.include_isort).lower()}
include_git_secrets = {str(config.tools.include_git_secrets).lower()}  # pragma: allowlist secret
include_osv_scanner = {str(config.tools.include_osv_scanner).lower()}
include_safety = {str(config.tools.include_safety).lower()}"""


def render_editorconfig() -> str:
    return """root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 4
trim_trailing_whitespace = true

[*.md]
trim_trailing_whitespace = false"""


def render_env_example(project: ProjectAnalysis) -> str:
    base = [
        "ENVIRONMENT=development",
        "LOG_LEVEL=INFO",
        "SECRET_KEY=change-me",
    ]
    if project.kind is ProjectKind.FASTAPI:
        base.extend(
            [
                "APP_HOST=0.0.0.0",
                "APP_PORT=8000",
                "DATABASE_URL=postgresql+psycopg://postgres@localhost:5432/app",
                "CORS_ALLOWED_ORIGINS=http://localhost:3000",
            ]
        )
    elif project.kind is ProjectKind.DJANGO:
        base.extend(
            [
                "DJANGO_SETTINGS_MODULE=config.settings.production",
                "DATABASE_URL=postgres://postgres@localhost:5432/app",
                "ALLOWED_HOSTS=localhost,127.0.0.1",
                "CSRF_TRUSTED_ORIGINS=https://example.com",
            ]
        )
    else:
        base.append("DATABASE_URL=postgresql://postgres@localhost:5432/app")
    return "\n".join(base)


def render_gitignore_block() -> str:
    return """.venv/
venv/
env/
__pycache__/
.coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.backend-guard/"""


def render_makefile_block(project: ProjectAnalysis) -> str:
    backend_guard_runner = (
        "BACKEND_GUARD = $(shell "
        "if command -v uv >/dev/null 2>&1 && uv run backend-guard --help >/dev/null 2>&1; "
        'then echo "uv run backend-guard"; '
        "elif [ -x ./.venv/bin/backend-guard ] && "
        "./.venv/bin/backend-guard --help >/dev/null 2>&1; "
        "then echo ./.venv/bin/backend-guard; "
        "elif command -v backend-guard >/dev/null 2>&1; "
        "then echo backend-guard; "
        "elif command -v python3 >/dev/null 2>&1 && "
        "python3 -m backend_guard --help >/dev/null 2>&1; "
        'then echo "python3 -m backend_guard"; '
        "elif command -v python >/dev/null 2>&1 && "
        "python -m backend_guard --help >/dev/null 2>&1; "
        'then echo "python -m backend_guard"; '
        "else echo backend-guard; fi)"
    )
    framework_targets = []
    if project.kind is ProjectKind.DJANGO:
        framework_targets.extend(
            [
                "run:\n\tpython manage.py runserver",
                "deploy-check:\n\tpython manage.py check --deploy",
            ]
        )
    elif project.kind is ProjectKind.FASTAPI:
        framework_targets.extend(
            [
                "run:\n\tuvicorn app.main:app --reload",
                "health:\n\tcurl -fsS http://127.0.0.1:8000/health || exit 1",
            ]
        )

    targets = [
        backend_guard_runner,
        "guard-init:\n\t$(BACKEND_GUARD) init",
        "guard-audit:\n\t$(BACKEND_GUARD) audit",
        "guard-fix:\n\t$(BACKEND_GUARD) fix",
        "guard-doctor:\n\t$(BACKEND_GUARD) doctor",
    ]
    targets.extend(framework_targets)
    return "\n\n".join(targets)


def render_github_actions(project: ProjectAnalysis) -> str:
    framework_hint = ""
    if project.kind is ProjectKind.DJANGO:
        framework_hint = """      - name: Django deploy checks
        run: uv run backend-guard audit
"""
    else:
        framework_hint = """      - name: Backend Guard audit
        run: uv run backend-guard audit
"""

    return f"""name: Backend Guard

on:
  push:
    branches: ["main", "master"]
  pull_request:

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: astral-sh/setup-uv@v4
      - name: Sync project environment
        run: uv sync --dev
      - name: Install project tooling
        run: uv run backend-guard install --yes
{framework_hint}"""


def managed_file_targets(root: Path) -> dict[str, Path]:
    return {
        "pre_commit": root / ".pre-commit-config.yaml",
        "ruff": root / "ruff.toml",
        "config": root / ".backend-guard.toml",
        "editorconfig": root / ".editorconfig",
        "env_example": root / ".env.example",
        "workflow": root / ".github" / "workflows" / "backend-guard.yml",
        "gitignore": root / ".gitignore",
        "makefile": root / "Makefile",
    }
