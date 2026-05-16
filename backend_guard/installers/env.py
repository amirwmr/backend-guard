"""Virtual environment creation helpers."""

from __future__ import annotations

from pathlib import Path

from backend_guard.core.models import CommandResult, PackageManagerAnalysis, VirtualEnvironment
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.environment import _python_path_for_env, resolve_system_python


def create_virtual_environment(
    root: Path,
    runner: CommandRunner,
    package_manager: PackageManagerAnalysis,
    *,
    dry_run: bool = False,
) -> tuple[VirtualEnvironment | None, CommandResult]:
    """Create a local .venv, preferring uv when available."""
    env_path = root / ".venv"
    uv_executable = runner.which("uv")
    if uv_executable:
        command = [uv_executable, "venv", "--seed", str(env_path)]
    else:
        system_python = resolve_system_python(runner)
        command = [str(system_python), "-m", "venv", str(env_path)]

    if dry_run:
        return (
            VirtualEnvironment(
                path=env_path,
                python_executable=_python_path_for_env(env_path),
                source="dry-run",
                manager=package_manager.manager,
            ),
            CommandResult(
                args=command, exit_code=0, stdout="Dry run: environment creation skipped."
            ),
        )

    result = runner.run(command, cwd=root)
    if not result.ok:
        return None, result
    return (
        VirtualEnvironment(
            path=env_path,
            python_executable=_python_path_for_env(env_path),
            source="created",
            manager=package_manager.manager,
        ),
        result,
    )
