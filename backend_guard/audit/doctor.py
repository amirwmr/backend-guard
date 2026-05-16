"""Doctor diagnostics."""

from __future__ import annotations

import sys

from backend_guard.core.constants import CONFIG_FILE_NAME, MIN_PYTHON_VERSION
from backend_guard.core.models import CheckStatus, DoctorCheck, ProjectAnalysis
from backend_guard.core.subprocess import CommandRunner
from backend_guard.utils.runtime import python_module_command


class DoctorService:
    """Diagnose common setup and tooling problems."""

    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def run(self, project: ProjectAnalysis) -> list[DoctorCheck]:
        checks: list[DoctorCheck] = []
        status = (
            CheckStatus.PASSED if sys.version_info[:2] >= MIN_PYTHON_VERSION else CheckStatus.FAILED
        )
        checks.append(
            DoctorCheck(
                name="python-version",
                status=status,
                detail=f"Running Python {sys.version.split()[0]}",
                remediation="Install Python 3.12+." if status is CheckStatus.FAILED else None,
            )
        )

        checks.append(
            DoctorCheck(
                name="virtual-environment",
                status=CheckStatus.PASSED if project.environment else CheckStatus.WARNING,
                detail=(
                    f"Detected environment at {project.environment.path}"
                    if project.environment
                    else "No project-local environment was detected."
                ),
                remediation="Run 'backend-guard init' to create .venv."
                if not project.environment
                else None,
            )
        )

        manager_ok = bool(
            project.package_manager
            and (
                project.package_manager.manager.value == "pip" or project.package_manager.executable
            )
        )
        checks.append(
            DoctorCheck(
                name="package-manager",
                status=CheckStatus.PASSED if manager_ok else CheckStatus.WARNING,
                detail=project.package_manager.reason
                if project.package_manager
                else "No package manager detected.",
                remediation="Install the detected package manager or use pip."
                if not manager_ok
                else None,
            )
        )

        hooks_ok = (project.root / ".git" / "hooks" / "pre-commit").exists()
        checks.append(
            DoctorCheck(
                name="git-hooks",
                status=CheckStatus.PASSED if hooks_ok else CheckStatus.WARNING,
                detail="pre-commit hook is installed."
                if hooks_ok
                else "pre-commit hook is missing.",
                remediation="Run 'backend-guard init' or 'python -m pre_commit install'."
                if not hooks_ok
                else None,
            )
        )

        config_ok = (project.root / CONFIG_FILE_NAME).exists()
        checks.append(
            DoctorCheck(
                name="config-file",
                status=CheckStatus.PASSED if config_ok else CheckStatus.WARNING,
                detail=f"{CONFIG_FILE_NAME} detected."
                if config_ok
                else f"{CONFIG_FILE_NAME} is missing.",
                remediation="Run 'backend-guard init' to generate the config."
                if not config_ok
                else None,
            )
        )

        pre_commit_result = self.runner.run(
            [*python_module_command(project.environment, "pre_commit"), "--version"],
            cwd=project.root,
        )
        checks.append(
            DoctorCheck(
                name="pre-commit",
                status=CheckStatus.PASSED if pre_commit_result.ok else CheckStatus.WARNING,
                detail=pre_commit_result.stdout.strip() or pre_commit_result.stderr.strip(),
                remediation="Run 'backend-guard install' to install pre-commit."
                if not pre_commit_result.ok
                else None,
            )
        )

        if project.package_manager and project.package_manager.lockfile:
            checks.append(
                DoctorCheck(
                    name="lockfile",
                    status=CheckStatus.PASSED,
                    detail=f"Detected {project.package_manager.lockfile.name}.",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name="lockfile",
                    status=CheckStatus.WARNING,
                    detail="No dependency lockfile detected.",
                    remediation="Commit uv.lock, poetry.lock, Pipfile.lock, or requirements.txt.",
                )
            )
        return checks
