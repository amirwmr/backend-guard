from __future__ import annotations

import os
from pathlib import Path

import pytest


def _venv_python_path(root: Path) -> Path:
    if os.name == "nt":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


@pytest.fixture()
def fastapi_project(tmp_path: Path) -> Path:
    project = tmp_path / "fastapi-service"
    project.mkdir()
    (project / "pyproject.toml").write_text(
        """
[project]
name = "fastapi-service"
version = "0.1.0"
dependencies = ["fastapi>=0.115", "uvicorn>=0.30"]
""".strip(),
        encoding="utf-8",
    )
    app_dir = project / "app"
    app_dir.mkdir()
    (app_dir / "main.py").write_text(
        """
from fastapi import FastAPI

app = FastAPI()


@app.get("/items")
async def items() -> dict[str, bool]:
    return {"ok": True}
""".strip(),
        encoding="utf-8",
    )
    return project


@pytest.fixture()
def django_project(tmp_path: Path) -> Path:
    project = tmp_path / "django-service"
    project.mkdir()
    (project / "manage.py").write_text(
        """
#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    sys.exit(0)
""".strip(),
        encoding="utf-8",
    )
    config_dir = project / "config"
    config_dir.mkdir()
    (config_dir / "settings.py").write_text(
        """
DEBUG = True
INSTALLED_APPS = ["django.contrib.auth"]
MIDDLEWARE = []
""".strip(),
        encoding="utf-8",
    )
    (project / "requirements.txt").write_text("Django==5.1.0\n", encoding="utf-8")
    return project


@pytest.fixture()
def project_with_venv(tmp_path: Path) -> Path:
    project = tmp_path / "venv-project"
    project.mkdir()
    python_path = _venv_python_path(project)
    python_path.parent.mkdir(parents=True)
    python_path.write_text("", encoding="utf-8")
    (project / "pyproject.toml").write_text(
        """
[project]
name = "service"
version = "0.1.0"
""".strip(),
        encoding="utf-8",
    )
    return project
