from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from backend_guard.cli.app import app

runner = CliRunner()


def test_init_dry_run_succeeds(fastapi_project: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(fastapi_project), "--yes", "--dry-run", "init"],
    )
    assert result.exit_code == 0
    assert "Project Detection" in result.output
    assert "Generated Files" in result.output
