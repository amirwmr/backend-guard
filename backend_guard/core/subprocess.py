"""Secure subprocess helpers."""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import time
from collections.abc import Mapping
from pathlib import Path

from backend_guard.core.constants import DEFAULT_TIMEOUT_SECONDS
from backend_guard.core.models import CommandResult


class CommandRunner:
    """Execute subprocesses without invoking a shell."""

    def __init__(self, *, verbose: bool = False) -> None:
        self.verbose = verbose

    def which(self, executable: str) -> str | None:
        return shutil.which(executable)

    def run(
        self,
        args: list[str],
        *,
        cwd: Path | None = None,
        env: Mapping[str, str] | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> CommandResult:
        executable = args[0]
        if self.which(executable) is None and not Path(executable).exists():
            return CommandResult(
                args=args,
                exit_code=127,
                stderr=f"Executable not found: {executable}",
                executable_found=False,
            )

        start = time.perf_counter()
        # Commands are executed with shell=False and an explicit argv list.
        completed = subprocess.run(  # nosec B603
            args,
            cwd=str(cwd) if cwd else None,
            env=dict(env) if env else None,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        duration_ms = int((time.perf_counter() - start) * 1000)
        return CommandResult(
            args=args,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_ms=duration_ms,
        )
