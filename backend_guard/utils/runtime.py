"""Runtime helpers for resolving project-local executables."""

from __future__ import annotations

import os
import sys

from backend_guard.core.models import VirtualEnvironment


def resolve_env_executable(environment: VirtualEnvironment | None, command: str) -> str:
    """Resolve a command inside a virtual environment when available."""
    if environment is None:
        return command

    bin_dir = environment.path / ("Scripts" if os.name == "nt" else "bin")
    candidates = [bin_dir / command]
    if os.name == "nt":
        candidates.extend([bin_dir / f"{command}.exe", bin_dir / f"{command}.cmd"])

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return command


def resolve_python_executable(environment: VirtualEnvironment | None) -> str:
    """Resolve the preferred Python interpreter."""
    if environment is not None:
        return str(environment.python_executable)
    return sys.executable or "python"


def python_module_command(environment: VirtualEnvironment | None, module: str) -> list[str]:
    """Build a python -m command using the best available interpreter."""
    return [resolve_python_executable(environment), "-m", module]
