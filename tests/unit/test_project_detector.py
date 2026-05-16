from __future__ import annotations

from pathlib import Path

from backend_guard.core.models import ProjectKind
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.project import detect_project


def test_detects_fastapi_project(fastapi_project: Path) -> None:
    result = detect_project(fastapi_project, CommandRunner())
    assert result.kind is ProjectKind.FASTAPI
    assert result.confidence > 0


def test_detects_django_project(django_project: Path) -> None:
    result = detect_project(django_project, CommandRunner())
    assert result.kind is ProjectKind.DJANGO
    assert result.manage_py is not None


def test_detects_generic_backend(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("sqlalchemy==2.0.0\nalembic==1.13.0\n", encoding="utf-8")
    (tmp_path / "service.py").write_text("import sqlalchemy\n", encoding="utf-8")
    result = detect_project(tmp_path, CommandRunner())
    assert result.kind is ProjectKind.GENERIC
