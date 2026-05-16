# Backend Guard

`backend-guard` is a production-minded CLI for Python backend teams that want secure pre-commit defaults, dependency auditing, and framework-aware project checks without hand-assembling half a dozen tools every time a new repository starts.

It detects Django, FastAPI, and generic Python backend services, understands common Python packaging ecosystems, creates or reuses local virtual environments, installs strict quality tooling, and gives teams a consistent `init -> audit -> fix -> doctor -> update` workflow.

## Highlights

- Detects FastAPI, Django, and generic backend projects from dependencies, imports, lockfiles, and layout signals.
- Detects `.venv`, `venv`, `env`, Poetry environments, Pipenv environments, and active `VIRTUAL_ENV`.
- Prefers `uv` for environment creation and falls back to `python -m venv`.
- Supports `uv`, `pip`, `poetry`, `pipenv`, `requirements.txt`, and `pyproject.toml` workflows.
- Generates secure pre-commit defaults with Ruff, pyupgrade, Bandit, detect-secrets, and dependency auditing.
- Adds `.editorconfig`, `.env.example`, `.gitignore` improvements, a Makefile block, and an optional GitHub Actions workflow.
- Runs project-aware audits with categorized findings, remediation guidance, and JSON output.
- Applies safe automated fixes only.
- Includes unit, CLI, integration, and snapshot-style tests.

## Install

### One-line install

```bash
curl -fsSL https://example.com/install.sh | bash
```

### Windows PowerShell

```powershell
irm https://example.com/install.ps1 | iex
```

### Direct package installs

```bash
pipx install backend-guard
```

```bash
uv tool install backend-guard
```

```bash
python -m pip install --user backend-guard
```

The shell installer prefers `uv tool install`, then `pipx`, then `pip --user`. WSL uses the Linux shell installer path.

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

### Common flags

- `--root`: inspect a specific project directory
- `--yes`: accept prompts automatically
- `--json`: emit JSON for machine-readable commands
- `--dry-run`: preview actions without touching files
- `--verbose`: show more execution detail

## What `init` does

`backend-guard init` will:

1. Detect the framework, package manager, and environment.
2. Offer to create `.venv` when no environment exists.
3. Install dev tooling into the current project ecosystem.
4. Generate or update:
   - `.pre-commit-config.yaml`
   - `ruff.toml`
   - `.backend-guard.toml`
   - `.editorconfig`
   - `.env.example`
   - `.github/workflows/backend-guard.yml`
   - managed blocks in `.gitignore` and `Makefile`
5. Install Git hooks when the repository is under Git.
6. Print framework-specific recommendations for FastAPI or Django.

## Generated defaults

### Pre-commit

The generated `.pre-commit-config.yaml` includes:

- `pre-commit-hooks`
- `ruff`
- `ruff-format`
- `pyupgrade`
- `bandit`
- `detect-secrets`
- `pip-audit`

Optional toggles in `.backend-guard.toml` allow enabling Black, isort, Safety, git-secrets, and OSV scanner hooks.

### Audit coverage

`backend-guard audit` checks:

- environment health
- package manager sanity
- lockfile presence
- Git status and merge-conflict markers
- Ruff lint results
- Bandit findings
- dependency vulnerabilities through `pip-audit`
- secret exposure candidates with `detect-secrets`
- Django deploy checks and dangerous Django settings
- FastAPI heuristics such as lifespan usage, wildcard CORS, and health endpoints

## Architecture

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

### Key design choices

- Python 3.12+
- Typer for command UX
- Rich for rendering
- Pydantic for typed configuration and report models
- safe `subprocess.run(..., shell=False)` everywhere
- atomic file writes for managed files
- explicit overwrite protection for unmanaged configs

## Example usage

```bash
backend-guard --root /path/to/service init --yes
backend-guard audit
backend-guard fix
backend-guard doctor --json
```

## Configuration

Project-local configuration lives in `.backend-guard.toml`.

An example config is included at [example-configs/backend-guard.toml](./example-configs/backend-guard.toml).

## Testing

Run the local test suite with:

```bash
python -m pip install -e ".[dev]"
pytest
```

The suite includes:

- detector unit tests
- filesystem safety tests
- CLI tests via Typer's `CliRunner`
- integration tests for file generation and uninstall flow
- a snapshot-style audit regression test

## Packaging and release

The project ships as a standard Python package with a console entrypoint:

- PyPI-friendly `pyproject.toml`
- `pipx` and `uv tool install` support
- shell and PowerShell installers
- GitHub Actions CI
- self-uninstall support for installer-managed installations

## Uninstall

Remove project integration:

```bash
backend-guard uninstall
```

Attempt to remove the CLI itself when installed via the installer manifest:

```bash
backend-guard uninstall --self
```

If you installed with `pipx`, you can also use:

```bash
pipx uninstall backend-guard
```
