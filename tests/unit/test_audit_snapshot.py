from __future__ import annotations

import json
from pathlib import Path

from backend_guard.audit.service import AuditService
from backend_guard.core.config import BackendGuardConfig
from backend_guard.core.subprocess import CommandRunner
from backend_guard.detectors.project import detect_project


def test_fastapi_audit_matches_snapshot(fastapi_project: Path) -> None:
    config = BackendGuardConfig.model_validate(
        {
            "checks": {
                "lint": False,
                "format": False,
                "security": False,
                "dependencies": False,
                "secrets": False,
                "git": False,
                "framework": False,
                "doctor": True,
            }
        }
    )
    report = AuditService(CommandRunner()).run(
        detect_project(fastapi_project, CommandRunner()),
        config,
    )
    payload = report.to_json_dict()
    payload["generated_at"] = "<normalized>"
    payload["root"] = "<normalized>"
    payload["sections"][0]["findings"][0]["detail"] = "<normalized>"

    snapshot_path = Path(__file__).resolve().parents[1] / "snapshots" / "fastapi_audit.json"
    expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert payload == expected
