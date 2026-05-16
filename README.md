# Backend Guard

`backend-guard` is a production-focused CLI for Python backend repositories. It detects Django, FastAPI, and generic service projects, bootstraps strict development tooling, installs secure pre-commit hooks, and provides a repeatable audit/fix/doctor workflow with minimal setup.

This repository is developed and tested with `uv`, and the local contributor workflow is `uv`-first.

## What it does

- Detects Django, FastAPI, and generic Python backend repositories from lockfiles, manifests, imports, and filesystem layout.
- Detects project environments from `.venv`, `venv`, `env`, Poetry, Pipenv, `uv`, and `VIRTUAL_ENV`.
- Prefers `uv` for environment creation and package management.
- Generates strict defaults for:
  - `.pre-commit-config.yaml`
  - `ruff.toml`
  - `.backend-guard.toml`
  - `.editorconfig`
  - `.env.example`
  - managed blocks in `.gitignore` and `Makefile`
  - `.github/workflows/backend-guard.yml`
- Runs structured repository audits across linting, secrets, dependencies, Git hygiene, and framework-specific checks.
- Applies safe automatic fixes without silently rewriting risky code.

## Commands

```bash
backend-guard init
backend-guard install
backend-guard audit
backend-guard fix
backend-guard doctor
backend-guard update
backend-guard uninstall
```

Useful global flags:

- `--root`
- `--yes`
- `--json`
- `--dry-run`
- `--verbose`

## Install

### Preferred

```bash
uv tool install backend-guard
```

### Also supported

```bash
pipx install backend-guard
```

```bash
python -m pip install --user backend-guard
```

### Installer scripts

Shell and PowerShell installers are included in [scripts/install.sh](./scripts/install.sh) and [scripts/install.ps1](./scripts/install.ps1).

Example published usage after release hosting is in place:

```bash
curl -fsSL https://example.com/install.sh | bash
```

```powershell
irm https://example.com/install.ps1 | iex
```

## Quick start

Bootstrap a backend project:

```bash
backend-guard init --yes
```

Audit it:

```bash
backend-guard audit
```

Apply safe automatic fixes:

```bash
backend-guard fix
```

Diagnose local setup issues:

```bash
backend-guard doctor
```

## Local development

This repository uses `uv` for local development.

Create or refresh the environment:

```bash
uv sync --dev
```

Run the test suite:

```bash
uv run pytest
```

Run the CLI from the working tree:

```bash
uv run backend-guard --help
```

Run the convenience targets:

```bash
make guard-audit
make guard-fix
make guard-doctor
```

The generated `Makefile` prefers `uv run backend-guard ...` automatically when `uv` is available.

## What `init` sets up

`backend-guard init` will:

1. Detect the project type, package manager, and current environment.
2. Offer to create `.venv` when no local environment exists.
3. Install project tooling into the detected ecosystem.
4. Generate or update managed configuration files.
5. Install Git hooks when the repository is under Git.
6. Print framework-aware recommendations for Django and FastAPI projects.

## Tooling defaults

### Pre-commit

The generated pre-commit configuration includes:

- `pre-commit-hooks`
- `ruff`
- `ruff-format`
- `pyupgrade`
- `bandit`
- `detect-secrets`
- `pip-audit`

Optional toggles in `.backend-guard.toml` can enable:

- Black
- isort
- Safety
- git-secrets
- OSV scanner

### Audit coverage

`backend-guard audit` checks:

- environment health
- package manager and lockfile state
- Git working tree hygiene
- merge-conflict markers
- Ruff lint results
- Bandit findings
- `pip-audit` vulnerability results
- `detect-secrets` findings
- Django deploy checks and risky settings
- FastAPI conventions such as lifespan usage, CORS posture, and health endpoints

## Repository layout

```text
backend_guard/
    cli/
    core/
    detectors/
    installers/
    audit/
    fixers/
    templates/
    utils/
tests/
scripts/
example-configs/
.github/workflows/
```

## Configuration

Project-local configuration lives in `.backend-guard.toml`.

An example is included in [example-configs/backend-guard.toml](./example-configs/backend-guard.toml).

## CI and release workflow

This repository uses `uv` in CI:

- [ci.yml](./.github/workflows/ci.yml) runs `uv sync --dev`, `uv run pytest`, and a CLI smoke test.
- [backend-guard.yml](./.github/workflows/backend-guard.yml) runs the repo’s own guard workflow with `uv`.
- [release.yml](./.github/workflows/release.yml) builds distributions with `uv build` and validates them with Twine.

## Publishing

The package is ready for:

- PyPI publishing
- `uv tool install`
- `pipx install`
- GitHub Releases
- shell and PowerShell installer distribution

## Uninstall

Remove managed project files:

```bash
backend-guard uninstall
```

Attempt to remove the CLI itself when installed via the installer manifest:

```bash
backend-guard uninstall --self
```
