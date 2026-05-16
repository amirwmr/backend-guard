"""Package manager detection."""

from __future__ import annotations

import tomllib
from pathlib import Path

from backend_guard.core.models import PackageManager, PackageManagerAnalysis
from backend_guard.core.subprocess import CommandRunner


def _load_pyproject(pyproject_path: Path) -> dict:
    if not pyproject_path.exists():
        return {}
    with pyproject_path.open("rb") as handle:
        return tomllib.load(handle)


def find_requirements_files(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in ("requirements*.txt", "requirements/*.txt"):
        candidates.extend(sorted(root.glob(pattern)))
    return [path for path in candidates if path.is_file()]


def detect_package_manager(root: Path, runner: CommandRunner) -> PackageManagerAnalysis:
    """Detect the project package manager from lockfiles and configuration."""
    pyproject_path = root / "pyproject.toml"
    pyproject = _load_pyproject(pyproject_path)

    if (root / "uv.lock").exists() or "uv" in pyproject.get("tool", {}):
        return PackageManagerAnalysis(
            manager=PackageManager.UV,
            executable=runner.which("uv"),
            reason="Detected uv.lock or [tool.uv] configuration.",
            lockfile=root / "uv.lock" if (root / "uv.lock").exists() else None,
            config_file=pyproject_path if pyproject_path.exists() else None,
        )

    if (root / "poetry.lock").exists() or "poetry" in pyproject.get("tool", {}):
        return PackageManagerAnalysis(
            manager=PackageManager.POETRY,
            executable=runner.which("poetry"),
            reason="Detected poetry.lock or [tool.poetry] configuration.",
            lockfile=root / "poetry.lock" if (root / "poetry.lock").exists() else None,
            config_file=pyproject_path if pyproject_path.exists() else None,
        )

    if (root / "Pipfile").exists():
        return PackageManagerAnalysis(
            manager=PackageManager.PIPENV,
            executable=runner.which("pipenv"),
            reason="Detected Pipfile configuration.",
            lockfile=root / "Pipfile.lock" if (root / "Pipfile.lock").exists() else None,
            config_file=root / "Pipfile",
        )

    requirements_files = find_requirements_files(root)
    return PackageManagerAnalysis(
        manager=PackageManager.PIP,
        executable=runner.which("python") or runner.which("python3"),
        reason="Falling back to pip-compatible workflow.",
        lockfile=requirements_files[0] if requirements_files else None,
        config_file=pyproject_path if pyproject_path.exists() else None,
    )
