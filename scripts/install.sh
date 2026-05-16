#!/usr/bin/env bash
set -euo pipefail

PACKAGE_SPEC="${BACKEND_GUARD_PACKAGE_SPEC:-backend-guard}"
STATE_DIR="${HOME}/.backend-guard"
MANIFEST_PATH="${STATE_DIR}/install-manifest.json"
PYTHON_BIN="$(command -v python3 || command -v python || true)"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "backend-guard installer requires python3 or python on PATH." >&2
  exit 1
fi

mkdir -p "${STATE_DIR}"

METHOD=""
UNINSTALL_JSON=""

if command -v uv >/dev/null 2>&1; then
  uv tool install --upgrade "${PACKAGE_SPEC}"
  METHOD="uv-tool"
  UNINSTALL_JSON='["uv","tool","uninstall","backend-guard"]'
elif command -v pipx >/dev/null 2>&1; then
  pipx install --force "${PACKAGE_SPEC}"
  METHOD="pipx"
  UNINSTALL_JSON='["pipx","uninstall","backend-guard"]'
else
  "${PYTHON_BIN}" -m pip install --user --upgrade "${PACKAGE_SPEC}"
  METHOD="pip-user"
  UNINSTALL_JSON="[\"${PYTHON_BIN}\",\"-m\",\"pip\",\"uninstall\",\"-y\",\"backend-guard\"]"
fi

export MANIFEST_PATH METHOD UNINSTALL_JSON
"${PYTHON_BIN}" - <<'PY'
import json
import os
from pathlib import Path

manifest_path = Path(os.environ["MANIFEST_PATH"])
manifest_path.parent.mkdir(parents=True, exist_ok=True)
manifest = {
    "method": os.environ["METHOD"],
    "uninstall_command": json.loads(os.environ["UNINSTALL_JSON"]),
    "executable_path": None,
}
manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
PY

echo "backend-guard installed."
echo "Run 'backend-guard --help' once your shell PATH is refreshed."
