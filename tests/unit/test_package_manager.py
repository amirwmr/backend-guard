from __future__ import annotations

from pathlib import Path

from backend_guard.core.models import PackageManager
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.package_manager import detect_package_manager


def test_detects_uv_from_lockfile(tmp_path: Path) -> None:
    (tmp_path / "uv.lock").write_text("", encoding="utf-8")
    result = detect_package_manager(tmp_path, CommandRunner())
    assert result.manager is PackageManager.UV


def test_detects_poetry_from_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.poetry]
name = "svc"
version = "0.1.0"
""".strip(),
        encoding="utf-8",
    )
    result = detect_package_manager(tmp_path, CommandRunner())
    assert result.manager is PackageManager.POETRY


def test_falls_back_to_pip(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi==0.115.0\n", encoding="utf-8")
    result = detect_package_manager(tmp_path, CommandRunner())
    assert result.manager is PackageManager.PIP
