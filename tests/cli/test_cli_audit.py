from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from backend_guard.cli.app import app

runner = CliRunner()


def test_audit_json_output(fastapi_project: Path) -> None:
    result = runner.invoke(
        app,
        ["--root", str(fastapi_project), "--json", "audit"],
    )
    assert result.exit_code in {0, 1}
    payload = json.loads(result.output)
    assert payload["project_kind"] == "fastapi"
    assert payload["sections"]
