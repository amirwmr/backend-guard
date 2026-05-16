from __future__ import annotations

from pathlib import Path

from backend_guard.core.config import BackendGuardConfig
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.project import detect_project
from backend_guard.installers.project import ProjectBootstrapService


def test_write_and_uninstall_project_files(fastapi_project: Path) -> None:
    project = detect_project(fastapi_project, CommandRunner())
    service = ProjectBootstrapService(CommandRunner())
    write_results = service.write_project_files(project, BackendGuardConfig(), overwrite=False)
    assert (fastapi_project / ".pre-commit-config.yaml").exists()
    uninstall_results = service.uninstall_project(fastapi_project)

    assert any(result.action in {"created", "updated"} for result in write_results)
    assert any(result.action == "removed" for result in uninstall_results)
