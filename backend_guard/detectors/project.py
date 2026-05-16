"""Framework and project detection."""

from __future__ import annotations

import ast
import os
import tomllib
from pathlib import Path

from backend_guard.core.constants import (
    DJANGO_KEYWORDS,
    FASTAPI_KEYWORDS,
    GENERIC_BACKEND_KEYWORDS,
    SKIP_DIRECTORIES,
)
from backend_guard.core.models import ProjectAnalysis, ProjectKind
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.environment import detect_virtual_environment
from backend_guard.detectors.package_manager import detect_package_manager, find_requirements_files


def _load_pyproject_dependencies(pyproject_path: Path) -> list[str]:
    if not pyproject_path.exists():
        return []
    with pyproject_path.open("rb") as handle:
        pyproject = tomllib.load(handle)

    dependencies: set[str] = set()
    project = pyproject.get("project", {})
    for dependency in project.get("dependencies", []):
        dependencies.add(str(dependency).split(";")[0].strip().split()[0].lower())

    poetry_dependencies = pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})
    for package_name in poetry_dependencies:
        if package_name.lower() != "python":
            dependencies.add(package_name.lower())
    return sorted(dependencies)


def _load_requirements_dependencies(requirements_files: list[Path]) -> list[str]:
    dependencies: set[str] = set()
    for requirements_file in requirements_files:
        for line in requirements_file.read_text(encoding="utf-8").splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith(("#", "-r", "--")):
                continue
            dependencies.add(cleaned.split("==")[0].split(">=")[0].split("[")[0].lower())
    return sorted(dependencies)


def _iter_python_files(root: Path, *, limit: int = 250) -> list[Path]:
    python_files: list[Path] = []
    for current_root, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in SKIP_DIRECTORIES]
        for name in files:
            if not name.endswith(".py"):
                continue
            python_files.append(Path(current_root) / name)
            if len(python_files) >= limit:
                return python_files
    return python_files


def _scan_imports_and_text(python_files: list[Path]) -> tuple[set[str], list[str]]:
    imports: set[str] = set()
    snippets: list[str] = []
    for path in python_files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        snippets.append(content[:2000].lower())
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0].lower())
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0].lower())
    return imports, snippets


def _build_recommendations(kind: ProjectKind) -> list[str]:
    if kind is ProjectKind.FASTAPI:
        return [
            "Adopt FastAPI lifespan handlers instead of legacy startup/shutdown events.",
            "Centralize configuration with pydantic-settings and explicit environment models.",
            "Add structured request logging, security middleware, and a health endpoint contract.",
            (
                "Review CORS, rate limiting, Docker image hardening, and "
                "uvicorn/gunicorn worker settings."
            ),
        ]
    if kind is ProjectKind.DJANGO:
        return [
            "Run deploy-time checks regularly and enforce secure cookie and HSTS settings.",
            "Split settings by environment and load secrets from environment variables only.",
            (
                "Review DRF authentication defaults, logging, WhiteNoise, and "
                "gunicorn production settings."
            ),
        ]
    if kind is ProjectKind.GENERIC:
        return [
            "Standardize runtime entrypoints, dependency locking, and environment-based settings.",
            "Add structured logging, health checks, and CI quality gates early.",
        ]
    return []


def detect_project(root: Path, runner: CommandRunner) -> ProjectAnalysis:
    """Detect project type, package manager, dependencies, and environment."""
    package_manager = detect_package_manager(root, runner)
    environment = detect_virtual_environment(root, runner, package_manager)
    pyproject_path = root / "pyproject.toml"
    requirements_files = find_requirements_files(root)
    python_files = _iter_python_files(root)
    imports, snippets = _scan_imports_and_text(python_files)

    dependencies = sorted(
        {
            *_load_pyproject_dependencies(pyproject_path),
            *_load_requirements_dependencies(requirements_files),
        }
    )
    signals = {dependency.lower() for dependency in dependencies} | imports
    combined_text = "\n".join(snippets)

    django_score = 0
    fastapi_score = 0
    generic_score = 0
    reasons: list[str] = []

    manage_py = root / "manage.py"
    if manage_py.exists():
        django_score += 3
        reasons.append("Detected manage.py, a strong Django signal.")

    if any(keyword in signals for keyword in DJANGO_KEYWORDS):
        django_score += 2
        reasons.append("Detected Django-related dependencies or imports.")
    if any(keyword in signals for keyword in FASTAPI_KEYWORDS):
        fastapi_score += 2
        reasons.append("Detected FastAPI-related dependencies or imports.")
    if any(keyword in signals for keyword in GENERIC_BACKEND_KEYWORDS):
        generic_score += 1
        reasons.append("Detected common backend service dependencies.")

    if "fastapi(" in combined_text or "apirouter(" in combined_text:
        fastapi_score += 2
        reasons.append("Detected FastAPI application patterns in source files.")
    if "installed_apps" in combined_text or "middleware" in combined_text:
        django_score += 1
    if "asgi.py" in combined_text or "wsgi.py" in combined_text:
        generic_score += 1

    scores = {
        ProjectKind.DJANGO: django_score,
        ProjectKind.FASTAPI: fastapi_score,
        ProjectKind.GENERIC: generic_score,
    }
    kind = max(scores, key=scores.get)
    if scores[kind] <= 0:
        kind = ProjectKind.UNKNOWN
    confidence = min(scores.get(kind, 0) / 5, 0.99) if kind is not ProjectKind.UNKNOWN else 0.0

    return ProjectAnalysis(
        root=root,
        kind=kind,
        confidence=confidence,
        reasons=reasons,
        package_manager=package_manager,
        environment=environment,
        pyproject_path=pyproject_path if pyproject_path.exists() else None,
        requirements_files=requirements_files,
        manage_py=manage_py if manage_py.exists() else None,
        python_files_scanned=len(python_files),
        dependencies=dependencies,
        recommendations=_build_recommendations(kind),
    )
