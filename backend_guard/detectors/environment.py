"""Virtual environment detection and creation helpers."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from backend_guard.core.models import PackageManager, PackageManagerAnalysis, VirtualEnvironment
from backend_guard.core.subprocess import CommandRunner


def _python_path_for_env(path: Path) -> Path:
    if os.name == "nt":
        return path / "Scripts" / "python.exe"
    return path / "bin" / "python"


def resolve_system_python(runner: CommandRunner) -> Path:
    if sys.executable:
        return Path(sys.executable)
    return Path(runner.which("python3") or runner.which("python") or "python")


def detect_virtual_environment(
    root: Path,
    runner: CommandRunner,
    package_manager: PackageManagerAnalysis,
) -> VirtualEnvironment | None:
    """Locate the best matching virtual environment for the current project."""
    for candidate in (".venv", "venv", "env"):
        env_path = root / candidate
        python_path = _python_path_for_env(env_path)
        if python_path.exists():
            return VirtualEnvironment(
                path=env_path,
                python_executable=python_path,
                source=candidate,
                manager=package_manager.manager,
            )

    active_venv = os.environ.get("VIRTUAL_ENV")
    if active_venv:
        active_path = Path(active_venv)
        python_path = _python_path_for_env(active_path)
        if python_path.exists():
            return VirtualEnvironment(
                path=active_path,
                python_executable=python_path,
                source="VIRTUAL_ENV",
                manager=package_manager.manager,
            )

    if package_manager.manager is PackageManager.POETRY and package_manager.executable:
        result = runner.run([package_manager.executable, "env", "info", "-p"], cwd=root)
        poetry_env = Path(result.stdout.strip()) if result.ok and result.stdout.strip() else None
        if poetry_env:
            python_path = _python_path_for_env(poetry_env)
            if python_path.exists():
                return VirtualEnvironment(
                    path=poetry_env,
                    python_executable=python_path,
                    source="poetry",
                    manager=package_manager.manager,
                )

    if package_manager.manager is PackageManager.PIPENV and package_manager.executable:
        result = runner.run([package_manager.executable, "--venv"], cwd=root)
        pipenv_env = Path(result.stdout.strip()) if result.ok and result.stdout.strip() else None
        if pipenv_env:
            python_path = _python_path_for_env(pipenv_env)
            if python_path.exists():
                return VirtualEnvironment(
                    path=pipenv_env,
                    python_executable=python_path,
                    source="pipenv",
                    manager=package_manager.manager,
                )

    return None
