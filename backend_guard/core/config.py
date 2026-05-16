"""Configuration loading and defaults."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from backend_guard.core.constants import CONFIG_FILE_NAME


class FileSettings(BaseModel):
    editorconfig: bool = True
    env_example: bool = True
    gitignore: bool = True
    makefile: bool = True
    github_actions: bool = True


class CheckSettings(BaseModel):
    lint: bool = True
    format: bool = True
    security: bool = True
    dependencies: bool = True
    secrets: bool = True
    git: bool = True
    framework: bool = True
    doctor: bool = True


class ToolSettings(BaseModel):
    use_ruff_format: bool = True
    include_black: bool = False
    include_isort: bool = False
    include_git_secrets: bool = False
    include_osv_scanner: bool = False
    include_safety: bool = False


class BackendGuardConfig(BaseModel):
    version: int = 1
    files: FileSettings = Field(default_factory=FileSettings)
    checks: CheckSettings = Field(default_factory=CheckSettings)
    tools: ToolSettings = Field(default_factory=ToolSettings)


def load_backend_guard_config(root: Path) -> BackendGuardConfig:
    """Load .backend-guard.toml when present, otherwise return defaults."""
    config_path = root / CONFIG_FILE_NAME
    if not config_path.exists():
        return BackendGuardConfig()

    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    return BackendGuardConfig.model_validate(data)
