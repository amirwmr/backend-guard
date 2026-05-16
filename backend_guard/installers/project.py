"""Project initialization, update, and uninstall services."""

from __future__ import annotations

import json
from pathlib import Path

from backend_guard.core.config import BackendGuardConfig
from backend_guard.core.constants import (
    DEFAULT_DEV_PACKAGES,
    INSTALL_MANIFEST_NAME,
    MANAGED_BLOCK_FILES,
    MANAGED_FILES,
    STATE_DIR_NAME,
)
from backend_guard.core.models import (
    CommandResult,
    ManagedWriteResult,
    ProjectAnalysis,
    SelfInstallManifest,
)
from backend_guard.core.subprocess import CommandRunner
from backend_guard.templates.project_files import (
    managed_file_targets,
    render_backend_guard_config,
    render_editorconfig,
    render_env_example,
    render_github_actions,
    render_gitignore_block,
    render_makefile_block,
    render_pre_commit_config,
    render_ruff_toml,
)
from backend_guard.utils.filesystem import (
    remove_managed_block,
    remove_managed_file,
    upsert_managed_block,
    write_managed_file,
)
from backend_guard.utils.runtime import python_module_command


class ProjectBootstrapService:
    """Bootstrap project tooling and managed files."""

    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def install_tooling(
        self,
        project: ProjectAnalysis,
        config: BackendGuardConfig,
        *,
        dry_run: bool = False,
    ) -> CommandResult:
        packages = list(DEFAULT_DEV_PACKAGES)
        if config.tools.include_black:
            packages.append("black")
        if config.tools.include_isort:
            packages.append("isort")
        if config.tools.include_safety:
            packages.append("safety")

        manager = project.package_manager
        if manager is None:
            return CommandResult(args=[], exit_code=1, stderr="No package manager detected.")

        if manager.manager.value == "uv" and project.pyproject_path:
            command = [manager.executable or "uv", "add", "--dev", *packages]
        elif manager.manager.value == "poetry":
            command = [manager.executable or "poetry", "add", "--group", "dev", *packages]
        elif manager.manager.value == "pipenv":
            command = [manager.executable or "pipenv", "install", "--dev", *packages]
        else:
            ensurepip_result = self._ensure_pip_available(project, dry_run=dry_run)
            if ensurepip_result is not None and not ensurepip_result.ok:
                return ensurepip_result
            python_command = python_module_command(project.environment, "pip")
            command = [*python_command, "install", *packages]

        if dry_run:
            return CommandResult(
                args=command, exit_code=0, stdout="Dry run: tooling installation skipped."
            )
        return self.runner.run(command, cwd=project.root)

    def _ensure_pip_available(
        self,
        project: ProjectAnalysis,
        *,
        dry_run: bool = False,
    ) -> CommandResult | None:
        if project.environment is None:
            return None

        pip_check_command = [*python_module_command(project.environment, "pip"), "--version"]
        pip_check_result = self.runner.run(pip_check_command, cwd=project.root)
        if pip_check_result.ok:
            return None

        ensurepip_command = [
            str(project.environment.python_executable),
            "-m",
            "ensurepip",
            "--upgrade",
        ]
        if dry_run:
            return CommandResult(
                args=ensurepip_command,
                exit_code=0,
                stdout="Dry run: ensurepip bootstrap skipped.",
            )
        return self.runner.run(ensurepip_command, cwd=project.root)

    def write_project_files(
        self,
        project: ProjectAnalysis,
        config: BackendGuardConfig,
        *,
        overwrite: bool = False,
        dry_run: bool = False,
    ) -> list[ManagedWriteResult]:
        targets = managed_file_targets(project.root)
        results: list[ManagedWriteResult] = []

        results.append(
            write_managed_file(
                targets["pre_commit"],
                render_pre_commit_config(project, config),
                overwrite=overwrite,
                dry_run=dry_run,
            )
        )
        results.append(
            write_managed_file(
                targets["ruff"],
                render_ruff_toml(project),
                overwrite=overwrite,
                dry_run=dry_run,
            )
        )
        results.append(
            write_managed_file(
                targets["config"],
                render_backend_guard_config(config),
                overwrite=overwrite,
                dry_run=dry_run,
            )
        )

        if config.files.editorconfig:
            results.append(
                write_managed_file(
                    targets["editorconfig"],
                    render_editorconfig(),
                    overwrite=overwrite,
                    dry_run=dry_run,
                )
            )
        if config.files.env_example:
            results.append(
                write_managed_file(
                    targets["env_example"],
                    render_env_example(project),
                    overwrite=overwrite,
                    dry_run=dry_run,
                )
            )
        if config.files.github_actions:
            results.append(
                write_managed_file(
                    targets["workflow"],
                    render_github_actions(project),
                    overwrite=overwrite,
                    dry_run=dry_run,
                )
            )
        if config.files.gitignore:
            results.append(
                upsert_managed_block(
                    targets["gitignore"],
                    block_name="gitignore",
                    content=render_gitignore_block(),
                    dry_run=dry_run,
                )
            )
        if config.files.makefile:
            results.append(
                upsert_managed_block(
                    targets["makefile"],
                    block_name="makefile",
                    content=render_makefile_block(project),
                    dry_run=dry_run,
                )
            )
        return results

    def install_git_hooks(
        self, project: ProjectAnalysis, *, dry_run: bool = False
    ) -> CommandResult:
        if not (project.root / ".git").exists():
            return CommandResult(
                args=[],
                exit_code=0,
                stdout="Skipping hook installation because this is not a Git repository.",
            )
        command = [*python_module_command(project.environment, "pre_commit"), "install"]
        if dry_run:
            return CommandResult(
                args=command, exit_code=0, stdout="Dry run: hook installation skipped."
            )
        return self.runner.run(command, cwd=project.root)

    def update_project(
        self, project: ProjectAnalysis, *, dry_run: bool = False
    ) -> list[CommandResult]:
        commands: list[list[str]] = [
            [*python_module_command(project.environment, "pre_commit"), "autoupdate"],
            [*python_module_command(project.environment, "pre_commit"), "install"],
        ]
        if project.kind.value == "django" and project.manage_py:
            commands.append(
                [
                    str(project.environment.python_executable if project.environment else "python"),
                    "manage.py",
                    "check",
                    "--deploy",
                ]
            )

        results: list[CommandResult] = []
        for command in commands:
            if dry_run:
                results.append(
                    CommandResult(
                        args=command, exit_code=0, stdout="Dry run: update command skipped."
                    )
                )
            else:
                results.append(self.runner.run(command, cwd=project.root))
        return results

    def uninstall_project(self, root: Path, *, dry_run: bool = False) -> list[ManagedWriteResult]:
        results: list[ManagedWriteResult] = []
        for relative_path in sorted(MANAGED_FILES):
            results.append(remove_managed_file(root / relative_path, dry_run=dry_run))

        for relative_path in sorted(MANAGED_BLOCK_FILES):
            block_name = "gitignore" if relative_path == ".gitignore" else "makefile"
            results.append(
                remove_managed_block(root / relative_path, block_name=block_name, dry_run=dry_run)
            )
        return results

    def uninstall_self(self, *, dry_run: bool = False) -> CommandResult:
        manifest_path = Path.home() / STATE_DIR_NAME / INSTALL_MANIFEST_NAME
        if not manifest_path.exists():
            return CommandResult(
                args=[],
                exit_code=1,
                stderr=(
                    "No installation manifest found. If you installed with pipx, run "
                    "'pipx uninstall backend-guard'."
                ),
            )

        manifest = SelfInstallManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if not manifest.uninstall_command:
            return CommandResult(
                args=[],
                exit_code=1,
                stderr="Installation manifest is missing an uninstall command.",
            )

        if dry_run:
            return CommandResult(
                args=manifest.uninstall_command,
                exit_code=0,
                stdout="Dry run: self uninstall skipped.",
            )

        result = self.runner.run(manifest.uninstall_command)
        if result.ok:
            manifest_path.unlink(missing_ok=True)
        return result

    def write_install_manifest(self, manifest: SelfInstallManifest) -> Path:
        state_dir = Path.home() / STATE_DIR_NAME
        state_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = state_dir / INSTALL_MANIFEST_NAME
        manifest_path.write_text(
            json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8"
        )
        return manifest_path
