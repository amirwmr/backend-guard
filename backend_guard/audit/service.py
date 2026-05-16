"""Audit workflow implementation."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from backend_guard.core.config import BackendGuardConfig
from backend_guard.core.constants import CONFIG_FILE_NAME, MIN_PYTHON_VERSION, SKIP_DIRECTORIES
from backend_guard.core.models import (
    AuditFinding,
    AuditReport,
    AuditSection,
    CheckStatus,
    CommandResult,
    ProjectAnalysis,
    ProjectKind,
    Severity,
)
from backend_guard.core.subprocess import CommandRunner
from backend_guard.utils.runtime import (
    python_module_command,
    resolve_env_executable,
    resolve_python_executable,
)


def _module_missing(result: CommandResult) -> bool:
    return "No module named" in result.stderr or "ModuleNotFoundError" in result.stderr


def _count_merge_conflicts(root: Path) -> int:
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        if path.suffix not in {
            ".py",
            ".toml",
            ".yaml",
            ".yml",
            ".json",
            ".ini",
            ".cfg",
            ".env",
            ".txt",
        }:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = content.splitlines()
        has_start = any(re.match(r"^<<<<<<<(?: .*)?$", line) for line in lines)
        has_end = any(re.match(r"^>>>>>>> (?:.*)$", line) for line in lines)
        if has_start and has_end:
            count += 1
    return count


def _scanner_excludes() -> tuple[str, str]:
    excluded_directories = [
        ".venv",
        "venv",
        "env",
        "__pycache__",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "node_modules",
        "tests",
    ]
    bandit_excludes = ",".join(excluded_directories)
    detect_secrets_excludes = (
        r"(^|/)(\.venv|venv|env|__pycache__|\.git|\.mypy_cache|\.pytest_cache|"
        r"\.ruff_cache|\.tox|node_modules)(/|$)"
    )
    return bandit_excludes, detect_secrets_excludes


def _make_finding(
    *,
    category: str,
    title: str,
    detail: str,
    severity: Severity,
    status: CheckStatus,
    remediation: str | None = None,
    location: str | None = None,
    tool: str | None = None,
) -> AuditFinding:
    return AuditFinding(
        category=category,
        title=title,
        detail=detail,
        severity=severity,
        status=status,
        remediation=remediation,
        location=location,
        tool=tool,
    )


class AuditService:
    """Run code quality and security checks."""

    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def run(self, project: ProjectAnalysis, config: BackendGuardConfig) -> AuditReport:
        sections = [
            self._environment_section(project),
            self._structure_section(project),
        ]
        if config.checks.git:
            sections.append(self._git_section(project))
        if config.checks.lint or config.checks.security:
            sections.append(self._tooling_section(project, config))
        if config.checks.dependencies or config.checks.secrets:
            sections.append(self._supply_chain_section(project, config))
        if config.checks.framework:
            sections.append(self._framework_section(project))
        return AuditReport(
            root=project.root,
            project_kind=project.kind,
            sections=[section for section in sections if section.findings],
            metadata={
                "python_files_scanned": project.python_files_scanned,
                "package_manager": project.package_manager.manager.value
                if project.package_manager
                else None,
                "environment": str(project.environment.path) if project.environment else None,
            },
        )

    def _environment_section(self, project: ProjectAnalysis) -> AuditSection:
        findings: list[AuditFinding] = []
        python_result = self.runner.run(
            [resolve_python_executable(project.environment), "--version"]
        )
        if python_result.ok:
            version_output = python_result.stdout.strip() or python_result.stderr.strip()
            major, minor = sys.version_info[:2]
            status = (
                CheckStatus.PASSED if (major, minor) >= MIN_PYTHON_VERSION else CheckStatus.FAILED
            )
            severity = Severity.INFO if status is CheckStatus.PASSED else Severity.ERROR
            findings.append(
                _make_finding(
                    category="environment",
                    title="Python runtime",
                    detail=f"Detected {version_output}.",
                    severity=severity,
                    status=status,
                    remediation="Use Python 3.12 or newer for full backend-guard support.",
                )
            )

        if project.environment:
            findings.append(
                _make_finding(
                    category="environment",
                    title="Virtual environment",
                    detail=f"Using environment at {project.environment.path}.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        else:
            findings.append(
                _make_finding(
                    category="environment",
                    title="Virtual environment",
                    detail="No project-local virtual environment was detected.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Run 'backend-guard init' to create .venv automatically.",
                )
            )

        if project.package_manager and (
            project.package_manager.manager.value == "pip" or project.package_manager.executable
        ):
            findings.append(
                _make_finding(
                    category="environment",
                    title="Package manager",
                    detail=project.package_manager.reason,
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        else:
            manager_name = (
                project.package_manager.manager.value if project.package_manager else "unknown"
            )
            findings.append(
                _make_finding(
                    category="environment",
                    title="Package manager executable",
                    detail=f"Detected {manager_name}, but its executable is not available on PATH.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation=f"Install {manager_name} or switch to a pip-compatible workflow.",
                )
            )

        if project.package_manager and project.package_manager.lockfile:
            findings.append(
                _make_finding(
                    category="environment",
                    title="Dependency lockfile",
                    detail=f"Detected lockfile/config: {project.package_manager.lockfile}.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        else:
            findings.append(
                _make_finding(
                    category="environment",
                    title="Dependency lockfile",
                    detail="No dependency lockfile or requirements manifest was detected.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation=(
                        "Commit uv.lock, poetry.lock, Pipfile.lock, or a requirements file."
                    ),
                )
            )
        return AuditSection(name="Environment", findings=findings)

    def _structure_section(self, project: ProjectAnalysis) -> AuditSection:
        findings: list[AuditFinding] = []
        expected_files = {
            ".pre-commit-config.yaml": (
                "Run 'backend-guard init' to generate a secure pre-commit config."
            ),
            "ruff.toml": "Run 'backend-guard init' to generate Ruff defaults.",
            CONFIG_FILE_NAME: "Use .backend-guard.toml to tailor checks and generated files.",
            ".editorconfig": "Add editor defaults to reduce whitespace and newline drift.",
            ".env.example": "Document required environment variables without committing secrets.",
        }
        for filename, remediation in expected_files.items():
            path = project.root / filename
            if path.exists():
                findings.append(
                    _make_finding(
                        category="structure",
                        title=f"{filename} present",
                        detail=f"Found {filename}.",
                        severity=Severity.INFO,
                        status=CheckStatus.PASSED,
                        location=str(path),
                    )
                )
            else:
                findings.append(
                    _make_finding(
                        category="structure",
                        title=f"{filename} missing",
                        detail=f"{filename} is not present.",
                        severity=Severity.WARNING,
                        status=CheckStatus.WARNING,
                        remediation=remediation,
                    )
                )
        return AuditSection(name="Structure", findings=findings)

    def _git_section(self, project: ProjectAnalysis) -> AuditSection:
        findings: list[AuditFinding] = []
        if not (project.root / ".git").exists():
            findings.append(
                _make_finding(
                    category="git",
                    title="Git repository",
                    detail="The current directory is not a Git repository.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Initialize Git before relying on pre-commit hook installation.",
                )
            )
            return AuditSection(name="Git", findings=findings)

        status_result = self.runner.run(["git", "status", "--porcelain"], cwd=project.root)
        if status_result.ok and status_result.stdout.strip():
            findings.append(
                _make_finding(
                    category="git",
                    title="Working tree is dirty",
                    detail="Uncommitted changes are present.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Review working tree changes before a release or security audit.",
                    tool="git",
                )
            )
        else:
            findings.append(
                _make_finding(
                    category="git",
                    title="Working tree status",
                    detail="No uncommitted changes detected.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                    tool="git",
                )
            )

        merge_conflicts = _count_merge_conflicts(project.root)
        if merge_conflicts:
            findings.append(
                _make_finding(
                    category="git",
                    title="Merge conflict markers",
                    detail=f"Detected merge conflict markers in {merge_conflicts} file(s).",
                    severity=Severity.ERROR,
                    status=CheckStatus.FAILED,
                    remediation="Resolve conflict markers before committing or auditing further.",
                )
            )
        else:
            findings.append(
                _make_finding(
                    category="git",
                    title="Merge conflict markers",
                    detail="No merge conflict markers detected in source-controlled text files.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        return AuditSection(name="Git", findings=findings)

    def _tooling_section(
        self, project: ProjectAnalysis, config: BackendGuardConfig
    ) -> AuditSection:
        findings: list[AuditFinding] = []
        bandit_excludes, _ = _scanner_excludes()

        if config.checks.lint:
            ruff_result = self.runner.run(
                [
                    *python_module_command(project.environment, "ruff"),
                    "check",
                    ".",
                    "--output-format=json",
                ],
                cwd=project.root,
            )
            findings.extend(self._lint_findings_from_result("ruff", ruff_result))

        if config.checks.security:
            bandit_command = [
                *python_module_command(project.environment, "bandit"),
                "-r",
                ".",
                "-f",
                "json",
                "-q",
                "-x",
                bandit_excludes,
            ]
            if project.pyproject_path:
                bandit_command.extend(["-c", str(project.pyproject_path)])
            bandit_result = self.runner.run(bandit_command, cwd=project.root)
            findings.extend(self._bandit_findings_from_result(bandit_result))

        return AuditSection(name="Tooling", findings=findings)

    def _supply_chain_section(
        self, project: ProjectAnalysis, config: BackendGuardConfig
    ) -> AuditSection:
        findings: list[AuditFinding] = []
        _, detect_secrets_excludes = _scanner_excludes()

        if config.checks.dependencies:
            command = [*python_module_command(project.environment, "pip_audit"), "--format=json"]
            if project.requirements_files:
                command[3:3] = ["-r", str(project.requirements_files[0])]
            pip_audit_result = self.runner.run(command, cwd=project.root)
            findings.extend(self._pip_audit_findings_from_result(pip_audit_result))

        if config.checks.secrets:
            detect_secrets_result = self.runner.run(
                [
                    resolve_env_executable(project.environment, "detect-secrets"),
                    "scan",
                    "--all-files",
                    "--exclude-files",
                    detect_secrets_excludes,
                ],
                cwd=project.root,
            )
            findings.extend(self._detect_secrets_findings_from_result(detect_secrets_result))

        return AuditSection(name="Supply Chain", findings=findings)

    def _framework_section(self, project: ProjectAnalysis) -> AuditSection:
        findings: list[AuditFinding] = []
        if project.kind is ProjectKind.DJANGO:
            findings.extend(self._django_findings(project))
        elif project.kind is ProjectKind.FASTAPI:
            findings.extend(self._fastapi_findings(project))
        elif project.kind is ProjectKind.GENERIC:
            findings.append(
                _make_finding(
                    category="framework",
                    title="Generic backend detected",
                    detail=(
                        "No framework-specific checks were applicable; generic "
                        "backend heuristics were used."
                    ),
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        return AuditSection(name="Framework", findings=findings)

    def _lint_findings_from_result(self, tool: str, result: CommandResult) -> list[AuditFinding]:
        if _module_missing(result):
            return [
                _make_finding(
                    category="lint",
                    title=f"{tool} unavailable",
                    detail=result.stderr.strip(),
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation=f"Run 'backend-guard install' to install {tool}.",
                    tool=tool,
                )
            ]

        issues = []
        if result.stdout.strip():
            try:
                issues = json.loads(result.stdout)
            except json.JSONDecodeError:
                issues = []

        if result.ok or not issues:
            return [
                _make_finding(
                    category="lint",
                    title="Ruff lint checks",
                    detail="No Ruff issues reported.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                    tool=tool,
                )
            ]
        return [
            _make_finding(
                category="lint",
                title="Ruff lint issues",
                detail=f"Ruff reported {len(issues)} issue(s).",
                severity=Severity.ERROR,
                status=CheckStatus.FAILED,
                remediation=(
                    "Run 'backend-guard fix' or 'ruff check --fix' for safe automated fixes."
                ),
                tool=tool,
            )
        ]

    def _bandit_findings_from_result(self, result: CommandResult) -> list[AuditFinding]:
        if _module_missing(result):
            return [
                _make_finding(
                    category="security",
                    title="Bandit unavailable",
                    detail=result.stderr.strip(),
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Run 'backend-guard install' to install bandit.",
                    tool="bandit",
                )
            ]

        issues = []
        if result.stdout.strip():
            try:
                issues = json.loads(result.stdout).get("results", [])
            except json.JSONDecodeError:
                issues = []

        if not issues:
            return [
                _make_finding(
                    category="security",
                    title="Bandit security scan",
                    detail="Bandit did not report any findings.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                    tool="bandit",
                )
            ]
        return [
            _make_finding(
                category="security",
                title="Bandit security findings",
                detail=f"Bandit reported {len(issues)} potential issue(s).",
                severity=Severity.ERROR,
                status=CheckStatus.FAILED,
                remediation=(
                    "Review Bandit output and fix or explicitly suppress legitimate exceptions."
                ),
                tool="bandit",
            )
        ]

    def _pip_audit_findings_from_result(self, result: CommandResult) -> list[AuditFinding]:
        if _module_missing(result):
            return [
                _make_finding(
                    category="dependencies",
                    title="pip-audit unavailable",
                    detail=result.stderr.strip(),
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Run 'backend-guard install' to install pip-audit.",
                    tool="pip-audit",
                )
            ]

        vulnerabilities = 0
        if result.stdout.strip():
            try:
                report = json.loads(result.stdout)
                for dependency in report.get("dependencies", []):
                    vulnerabilities += len(dependency.get("vulns", []))
            except json.JSONDecodeError:
                vulnerabilities = 0

        if vulnerabilities == 0 and result.ok:
            return [
                _make_finding(
                    category="dependencies",
                    title="Dependency audit",
                    detail="pip-audit did not report known vulnerabilities.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                    tool="pip-audit",
                )
            ]
        if vulnerabilities == 0 and not result.ok:
            return [
                _make_finding(
                    category="dependencies",
                    title="Dependency audit could not complete",
                    detail=result.stderr.strip() or result.stdout.strip(),
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation=(
                        "Ensure the active environment can resolve and import project dependencies."
                    ),
                    tool="pip-audit",
                )
            ]
        return [
            _make_finding(
                category="dependencies",
                title="Dependency vulnerabilities detected",
                detail=f"pip-audit reported {vulnerabilities} vulnerability record(s).",
                severity=Severity.ERROR,
                status=CheckStatus.FAILED,
                remediation="Upgrade or pin affected dependencies and regenerate the lockfile.",
                tool="pip-audit",
            )
        ]

    def _detect_secrets_findings_from_result(self, result: CommandResult) -> list[AuditFinding]:
        if not result.executable_found:
            return [
                _make_finding(
                    category="secrets",
                    title="detect-secrets unavailable",
                    detail=result.stderr.strip(),
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Run 'backend-guard install' to install detect-secrets.",
                    tool="detect-secrets",
                )
            ]

        candidates = 0
        if result.stdout.strip():
            try:
                payload = json.loads(result.stdout)
                results_map = payload.get("results", {})
                candidates = sum(len(items) for items in results_map.values())
            except json.JSONDecodeError:
                candidates = 0

        if candidates == 0 and result.ok:
            return [
                _make_finding(
                    category="secrets",
                    title="Secret scan",
                    detail="detect-secrets did not report any candidate secrets.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                    tool="detect-secrets",
                )
            ]
        if candidates == 0 and not result.ok:
            return [
                _make_finding(
                    category="secrets",
                    title="Secret scan could not complete",
                    detail=result.stderr.strip() or result.stdout.strip(),
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation=(
                        "Verify detect-secrets is installed and the repository is readable."
                    ),
                    tool="detect-secrets",
                )
            ]
        return [
            _make_finding(
                category="secrets",
                title="Potential secrets detected",
                detail=f"detect-secrets reported {candidates} candidate secret(s).",
                severity=Severity.ERROR,
                status=CheckStatus.FAILED,
                remediation=(
                    "Review the findings, rotate exposed credentials, and add a baseline if needed."
                ),
                tool="detect-secrets",
            )
        ]

    def _django_findings(self, project: ProjectAnalysis) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        if project.manage_py:
            command = [
                str(
                    project.environment.python_executable if project.environment else sys.executable
                ),
                "manage.py",
                "check",
                "--deploy",
            ]
            result = self.runner.run(command, cwd=project.root)
            if result.ok:
                findings.append(
                    _make_finding(
                        category="framework",
                        title="Django deploy checks",
                        detail="manage.py check --deploy passed.",
                        severity=Severity.INFO,
                        status=CheckStatus.PASSED,
                        tool="django",
                    )
                )
            else:
                findings.append(
                    _make_finding(
                        category="framework",
                        title="Django deploy checks",
                        detail=result.stdout.strip() or result.stderr.strip(),
                        severity=Severity.ERROR,
                        status=CheckStatus.FAILED,
                        remediation=(
                            "Address Django deploy check findings before production release."
                        ),
                        tool="django",
                    )
                )

        settings_files = sorted(project.root.glob("**/settings*.py"))
        dangerous_patterns = {
            "DEBUG = True": "Disable DEBUG outside local development.",
            "SESSION_COOKIE_SECURE = False": (
                "Enable secure session cookies in production settings."
            ),
            "CSRF_COOKIE_SECURE = False": "Enable secure CSRF cookies in production settings.",
        }
        for settings_file in settings_files[:10]:
            content = settings_file.read_text(encoding="utf-8", errors="ignore")
            for pattern, remediation in dangerous_patterns.items():
                if pattern in content:
                    findings.append(
                        _make_finding(
                            category="framework",
                            title=f"Django setting risk: {pattern}",
                            detail=f"Detected '{pattern}' in {settings_file}.",
                            severity=Severity.WARNING,
                            status=CheckStatus.WARNING,
                            remediation=remediation,
                            location=str(settings_file),
                        )
                    )
        return findings

    def _fastapi_findings(self, project: ProjectAnalysis) -> list[AuditFinding]:
        findings: list[AuditFinding] = []
        python_files = sorted(project.root.rglob("*.py"))
        combined_text = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")[:4000].lower()
            for path in python_files
            if not any(part in SKIP_DIRECTORIES for part in path.parts)
        )

        if "lifespan=" in combined_text:
            findings.append(
                _make_finding(
                    category="framework",
                    title="FastAPI lifespan usage",
                    detail="Detected lifespan-based startup/shutdown management.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        else:
            findings.append(
                _make_finding(
                    category="framework",
                    title="FastAPI lifespan pattern",
                    detail="No lifespan handler was detected.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Prefer lifespan handlers over deprecated startup/shutdown events.",
                )
            )

        if 'allow_origins=["*"]' in combined_text or "allow_origins=['*']" in combined_text:
            findings.append(
                _make_finding(
                    category="framework",
                    title="Permissive CORS configuration",
                    detail="Detected wildcard CORS origins.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation="Restrict CORS to trusted frontend origins in production.",
                )
            )

        if "/health" in combined_text:
            findings.append(
                _make_finding(
                    category="framework",
                    title="Health endpoint",
                    detail="Detected a health endpoint route.",
                    severity=Severity.INFO,
                    status=CheckStatus.PASSED,
                )
            )
        else:
            findings.append(
                _make_finding(
                    category="framework",
                    title="Health endpoint",
                    detail="No health endpoint convention was detected.",
                    severity=Severity.WARNING,
                    status=CheckStatus.WARNING,
                    remediation=(
                        "Expose a lightweight health endpoint for probes and uptime checks."
                    ),
                )
            )
        return findings
