"""Rich console rendering helpers."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from backend_guard.core.models import (
    AuditReport,
    CommandResult,
    DoctorCheck,
    ManagedWriteResult,
    ProjectAnalysis,
)


def render_project_summary(console: Console, project: ProjectAnalysis) -> None:
    details = [
        f"Framework: [bold]{project.kind.value}[/bold]",
        f"Confidence: {project.confidence:.0%}",
        (
            "Package manager: "
            f"{project.package_manager.manager.value if project.package_manager else 'unknown'}"
        ),
        f"Environment: {project.environment.path if project.environment else 'not detected'}",
        f"Python files scanned: {project.python_files_scanned}",
    ]
    if project.reasons:
        details.append("Signals: " + "; ".join(project.reasons[:4]))
    console.print(Panel("\n".join(details), title="Project Detection", border_style="cyan"))


def render_write_results(
    console: Console, results: list[ManagedWriteResult], *, title: str
) -> None:
    table = Table(title=title)
    table.add_column("Path")
    table.add_column("Action")
    table.add_column("Backup")
    for result in results:
        table.add_row(str(result.path), result.action, str(result.backup_path or ""))
    console.print(table)


def render_command_results(console: Console, results: list[CommandResult], *, title: str) -> None:
    table = Table(title=title)
    table.add_column("Command")
    table.add_column("Exit")
    table.add_column("Summary")
    for result in results:
        summary = result.stdout.strip() or result.stderr.strip() or "Completed"
        table.add_row(" ".join(result.args), str(result.exit_code), summary[:120])
    console.print(table)


def render_audit_report(console: Console, report: AuditReport, *, as_json: bool = False) -> None:
    if as_json:
        console.print_json(json.dumps(report.to_json_dict(), indent=2))
        return

    for section in report.sections:
        table = Table(title=section.name)
        table.add_column("Status")
        table.add_column("Severity")
        table.add_column("Title")
        table.add_column("Detail")
        for finding in section.findings:
            table.add_row(
                finding.status.value,
                finding.severity.value,
                finding.title,
                finding.detail,
            )
        console.print(table)
    console.print(
        Panel(
            (
                f"Failed: {report.total_failed}\n"
                f"Warnings: {report.total_warnings}\n"
                f"Project: {report.project_kind.value}"
            ),
            title="Audit Summary",
            border_style="green" if report.exit_code == 0 else "red",
        )
    )


def render_doctor_checks(
    console: Console, checks: list[DoctorCheck], *, as_json: bool = False
) -> None:
    if as_json:
        console.print_json(
            json.dumps([check.model_dump(mode="json") for check in checks], indent=2)
        )
        return

    table = Table(title="Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    table.add_column("Remediation")
    for check in checks:
        table.add_row(check.name, check.status.value, check.detail, check.remediation or "")
    console.print(table)


def summarize_paths(paths: list[Path]) -> str:
    return ", ".join(str(path) for path in paths)
