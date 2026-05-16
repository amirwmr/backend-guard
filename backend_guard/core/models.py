"""Typed models used across the application."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ProjectKind(StrEnum):
    DJANGO = "django"
    FASTAPI = "fastapi"
    GENERIC = "generic-python-backend"
    UNKNOWN = "unknown"


class PackageManager(StrEnum):
    UV = "uv"
    POETRY = "poetry"
    PIPENV = "pipenv"
    PIP = "pip"


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class CheckStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class CommandResult(BaseModel):
    args: list[str]
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = 0
    executable_found: bool = True

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


class VirtualEnvironment(BaseModel):
    path: Path
    python_executable: Path
    source: str
    kind: str = "venv"
    manager: PackageManager | None = None

    @property
    def exists(self) -> bool:
        return self.python_executable.exists()


class PackageManagerAnalysis(BaseModel):
    manager: PackageManager
    executable: str | None = None
    reason: str
    lockfile: Path | None = None
    config_file: Path | None = None

    def install_dev_command(
        self,
        *,
        packages: list[str],
        python_executable: Path | None,
    ) -> list[str]:
        if self.manager is PackageManager.UV:
            return [self.executable or "uv", "add", "--dev", *packages]
        if self.manager is PackageManager.POETRY:
            return [self.executable or "poetry", "add", "--group", "dev", *packages]
        if self.manager is PackageManager.PIPENV:
            return [self.executable or "pipenv", "install", "--dev", *packages]
        python_bin = str(python_executable) if python_executable else "python"
        return [python_bin, "-m", "pip", "install", *packages]


class ProjectAnalysis(BaseModel):
    root: Path
    kind: ProjectKind = ProjectKind.UNKNOWN
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    package_manager: PackageManagerAnalysis | None = None
    environment: VirtualEnvironment | None = None
    pyproject_path: Path | None = None
    requirements_files: list[Path] = Field(default_factory=list)
    manage_py: Path | None = None
    python_files_scanned: int = 0
    dependencies: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class AuditFinding(BaseModel):
    category: str
    title: str
    detail: str
    severity: Severity
    status: CheckStatus
    remediation: str | None = None
    location: str | None = None
    tool: str | None = None


class AuditSection(BaseModel):
    name: str
    findings: list[AuditFinding] = Field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for finding in self.findings if finding.status is CheckStatus.PASSED)

    @property
    def failed(self) -> int:
        return sum(1 for finding in self.findings if finding.status is CheckStatus.FAILED)

    @property
    def warnings(self) -> int:
        return sum(1 for finding in self.findings if finding.status is CheckStatus.WARNING)


class AuditReport(BaseModel):
    root: Path
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    project_kind: ProjectKind
    sections: list[AuditSection] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def total_failed(self) -> int:
        return sum(section.failed for section in self.sections)

    @property
    def total_warnings(self) -> int:
        return sum(section.warnings for section in self.sections)

    @property
    def exit_code(self) -> int:
        return 1 if self.total_failed else 0

    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class ManagedWriteResult(BaseModel):
    path: Path
    action: str
    backup_path: Path | None = None
    changed: bool = False


class DoctorCheck(BaseModel):
    name: str
    status: CheckStatus
    detail: str
    remediation: str | None = None


class SelfInstallManifest(BaseModel):
    method: str
    uninstall_command: list[str] = Field(default_factory=list)
    executable_path: str | None = None
