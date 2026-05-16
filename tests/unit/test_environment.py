from __future__ import annotations

import os
from pathlib import Path

from backend_guard.core.models import PackageManager, PackageManagerAnalysis
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.environment import detect_virtual_environment


def test_detects_local_dot_venv(project_with_venv: Path) -> None:
    analysis = PackageManagerAnalysis(manager=PackageManager.PIP, reason="test")
    result = detect_virtual_environment(project_with_venv, CommandRunner(), analysis)
    assert result is not None
    assert result.source == ".venv"


def test_falls_back_to_active_virtual_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    active_env = tmp_path / "active-env"
    python_path = (
        active_env
        / ("Scripts" if os.name == "nt" else "bin")
        / ("python.exe" if os.name == "nt" else "python")
    )
    python_path.parent.mkdir(parents=True)
    python_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(active_env))

    analysis = PackageManagerAnalysis(manager=PackageManager.PIP, reason="test")
    result = detect_virtual_environment(project, CommandRunner(), analysis)

    assert result is not None
    assert result.source == "VIRTUAL_ENV"
