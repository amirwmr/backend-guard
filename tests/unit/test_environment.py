from __future__ import annotations

from pathlib import Path

from backend_guard.core.models import PackageManager, PackageManagerAnalysis
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.environment import detect_virtual_environment


def test_detects_local_dot_venv(project_with_venv: Path) -> None:
    analysis = PackageManagerAnalysis(manager=PackageManager.PIP, reason="test")
    result = detect_virtual_environment(project_with_venv, CommandRunner(), analysis)
    assert result is not None
    assert result.source == ".venv"
