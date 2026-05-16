"""Safe automatic fixers."""

from __future__ import annotations

from backend_guard.core.models import CommandResult, ProjectAnalysis
from backend_guard.core.subprocess import CommandRunner
from backend_guard.utils.runtime import python_module_command


class FixService:
    """Apply safe automated fixes only."""

    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def run(self, project: ProjectAnalysis, *, dry_run: bool = False) -> list[CommandResult]:
        commands = [
            [*python_module_command(project.environment, "ruff"), "check", ".", "--fix"],
            [*python_module_command(project.environment, "ruff"), "format", "."],
            [*python_module_command(project.environment, "pre_commit"), "run", "trailing-whitespace", "--all-files"],
            [*python_module_command(project.environment, "pre_commit"), "run", "end-of-file-fixer", "--all-files"],
            [*python_module_command(project.environment, "pre_commit"), "run", "mixed-line-ending", "--all-files"],
            [*python_module_command(project.environment, "pre_commit"), "run", "check-json", "--all-files"],
            [*python_module_command(project.environment, "pre_commit"), "run", "check-toml", "--all-files"],
            [*python_module_command(project.environment, "pre_commit"), "run", "check-yaml", "--all-files"],
            [*python_module_command(project.environment, "pre_commit"), "run", "pyupgrade", "--all-files"],
        ]

        results: list[CommandResult] = []
        for command in commands:
            if dry_run:
                results.append(
                    CommandResult(args=command, exit_code=0, stdout="Dry run: fix command skipped.")
                )
            else:
                results.append(self.runner.run(command, cwd=project.root))
        return results
