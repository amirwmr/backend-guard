"""Typer CLI application."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm

from backend_guard.audit.doctor import DoctorService
from backend_guard.audit.service import AuditService
from backend_guard.core.config import BackendGuardConfig, load_backend_guard_config
from backend_guard.core.exceptions import FileWriteDeclinedError
from backend_guard.core.models import CheckStatus, ProjectAnalysis
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.project import detect_project
from backend_guard.fixers.service import FixService
from backend_guard.installers.env import create_virtual_environment
from backend_guard.installers.project import ProjectBootstrapService
from backend_guard.templates.project_files import managed_file_targets
from backend_guard.utils.console import (
    render_audit_report,
    render_command_results,
    render_doctor_checks,
    render_project_summary,
    render_write_results,
)
from backend_guard.utils.filesystem import is_managed_file

app = typer.Typer(
    add_completion=False,
    help="Detect, secure, and standardize Python backend projects.",
    no_args_is_help=True,
)


@dataclass
class AppState:
    root: Path
    yes: bool
    verbose: bool
    json_output: bool
    dry_run: bool
    console: Console
    runner: CommandRunner


def _state(ctx: typer.Context) -> AppState:
    return ctx.obj


def _preflight_overwrite(project: ProjectAnalysis, config: BackendGuardConfig) -> list[Path]:
    targets = managed_file_targets(project.root)
    file_keys = ["pre_commit", "ruff", "config"]
    if config.files.editorconfig:
        file_keys.append("editorconfig")
    if config.files.env_example:
        file_keys.append("env_example")
    if config.files.github_actions:
        file_keys.append("workflow")

    conflicts: list[Path] = []
    for key in file_keys:
        path = targets[key]
        if path.exists() and not is_managed_file(path):
            conflicts.append(path)
    return conflicts


def _ensure_environment(state: AppState, project: ProjectAnalysis) -> ProjectAnalysis:
    if project.environment:
        return project

    should_create = state.yes or Confirm.ask(
        "No local virtual environment was detected. Create .venv now?", default=True
    )
    if not should_create:
        return project

    environment, result = create_virtual_environment(
        state.root,
        state.runner,
        project.package_manager,
        dry_run=state.dry_run,
    )
    state.console.print(result.stdout or result.stderr)
    if not result.ok:
        raise typer.Exit(code=1)
    if environment and state.dry_run:
        return project.model_copy(update={"environment": environment})
    if environment:
        return detect_project(state.root, state.runner)
    return project


@app.callback()
def main(
    ctx: typer.Context,
    root: Path = typer.Option(Path.cwd(), "--root", help="Project root to inspect."),
    yes: bool = typer.Option(False, "--yes", help="Assume yes for prompts."),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose command output."),
    json_output: bool = typer.Option(False, "--json", help="Render JSON output when supported."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview actions without changing files."
    ),
) -> None:
    """Initialize global application state."""
    console = Console()
    ctx.obj = AppState(
        root=root.resolve(),
        yes=yes,
        verbose=verbose,
        json_output=json_output,
        dry_run=dry_run,
        console=console,
        runner=CommandRunner(verbose=verbose),
    )


@app.command()
def init(ctx: typer.Context) -> None:
    """Detect the project, install tooling, and generate secure defaults."""
    state = _state(ctx)
    config = load_backend_guard_config(state.root)
    project = _ensure_environment(state, detect_project(state.root, state.runner))
    render_project_summary(state.console, project)

    conflicts = _preflight_overwrite(project, config)
    overwrite = False
    if conflicts:
        state.console.print("Existing unmanaged files would be overwritten:")
        for conflict in conflicts:
            state.console.print(f" - {conflict}")
        overwrite = state.yes or Confirm.ask(
            "Overwrite these files after backing them up?", default=False
        )
        if not overwrite:
            raise typer.Exit(code=1)

    bootstrap = ProjectBootstrapService(state.runner)
    install_result = bootstrap.install_tooling(project, config, dry_run=state.dry_run)
    if install_result.args:
        render_command_results(state.console, [install_result], title="Tooling Installation")

    try:
        write_results = bootstrap.write_project_files(
            project,
            config,
            overwrite=overwrite,
            dry_run=state.dry_run,
        )
    except FileWriteDeclinedError as exc:
        state.console.print(str(exc), style="red")
        raise typer.Exit(code=1) from exc
    render_write_results(state.console, write_results, title="Generated Files")

    hook_result = bootstrap.install_git_hooks(project, dry_run=state.dry_run)
    render_command_results(state.console, [hook_result], title="Git Hooks")

    if project.recommendations:
        state.console.print("[bold]Framework Recommendations[/bold]")
        for recommendation in project.recommendations:
            state.console.print(f" - {recommendation}")


@app.command()
def install(ctx: typer.Context) -> None:
    """Install backend-guard project tooling into the detected environment."""
    state = _state(ctx)
    config = load_backend_guard_config(state.root)
    project = _ensure_environment(state, detect_project(state.root, state.runner))
    bootstrap = ProjectBootstrapService(state.runner)
    result = bootstrap.install_tooling(project, config, dry_run=state.dry_run)
    render_command_results(state.console, [result], title="Install")
    raise typer.Exit(code=0 if result.ok else 1)


@app.command()
def audit(ctx: typer.Context) -> None:
    """Run lint, security, dependency, and project sanity checks."""
    state = _state(ctx)
    config = load_backend_guard_config(state.root)
    project = detect_project(state.root, state.runner)
    report = AuditService(state.runner).run(project, config)
    render_audit_report(state.console, report, as_json=state.json_output)
    raise typer.Exit(code=report.exit_code)


@app.command()
def fix(ctx: typer.Context) -> None:
    """Apply safe automated fixes only."""
    state = _state(ctx)
    project = detect_project(state.root, state.runner)
    results = FixService(state.runner).run(project, dry_run=state.dry_run)
    render_command_results(state.console, results, title="Fixes")
    exit_code = 0 if all(result.ok for result in results) else 1
    raise typer.Exit(code=exit_code)


@app.command()
def doctor(ctx: typer.Context) -> None:
    """Diagnose environment, hook, and configuration issues."""
    state = _state(ctx)
    project = detect_project(state.root, state.runner)
    checks = DoctorService(state.runner).run(project)
    render_doctor_checks(state.console, checks, as_json=state.json_output)
    exit_code = 0 if all(check.status is not CheckStatus.FAILED for check in checks) else 1
    raise typer.Exit(code=exit_code)


@app.command()
def update(ctx: typer.Context) -> None:
    """Update managed hook versions and refresh installed hooks."""
    state = _state(ctx)
    project = detect_project(state.root, state.runner)
    results = ProjectBootstrapService(state.runner).update_project(project, dry_run=state.dry_run)
    render_command_results(state.console, results, title="Update")
    exit_code = 0 if all(result.ok for result in results) else 1
    raise typer.Exit(code=exit_code)


@app.command()
def uninstall(
    ctx: typer.Context,
    project: bool = typer.Option(
        True, "--project/--no-project", help="Remove project integration files."
    ),
    self_uninstall: bool = typer.Option(
        False, "--self", help="Uninstall the backend-guard CLI itself."
    ),
) -> None:
    """Remove generated project files and optionally uninstall the CLI."""
    state = _state(ctx)
    bootstrap = ProjectBootstrapService(state.runner)
    if project:
        write_results = bootstrap.uninstall_project(state.root, dry_run=state.dry_run)
        render_write_results(state.console, write_results, title="Project Uninstall")
    if self_uninstall:
        result = bootstrap.uninstall_self(dry_run=state.dry_run)
        render_command_results(state.console, [result], title="Self Uninstall")
