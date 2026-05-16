"""Filesystem helpers for safe, atomic writes."""

from __future__ import annotations

import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from backend_guard.core.constants import MANAGED_MARKER
from backend_guard.core.exceptions import FileWriteDeclinedError
from backend_guard.core.models import ManagedWriteResult


def atomic_write_text(path: Path, content: str) -> None:
    """Write text atomically to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(content)
        temp_name = handle.name
    os.replace(temp_name, path)


def backup_file(path: Path) -> Path:
    """Create a timestamped backup of an existing file."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak.{timestamp}")
    backup_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def managed_content(content: str, *, comment_prefix: str = "#") -> str:
    header = f"{comment_prefix} {MANAGED_MARKER}"
    return f"{header}\n{content.rstrip()}\n"


def is_managed_file(path: Path) -> bool:
    if not path.exists():
        return False
    first_line = path.read_text(encoding="utf-8").splitlines()[:1]
    return bool(first_line and MANAGED_MARKER in first_line[0])


def write_managed_file(
    path: Path,
    content: str,
    *,
    comment_prefix: str = "#",
    overwrite: bool = False,
    dry_run: bool = False,
) -> ManagedWriteResult:
    rendered = managed_content(content, comment_prefix=comment_prefix)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == rendered:
            return ManagedWriteResult(path=path, action="unchanged", changed=False)
        if not is_managed_file(path) and not overwrite:
            raise FileWriteDeclinedError(
                f"{path} already exists and is not managed by backend-guard."
            )
        backup_path = None if dry_run else backup_file(path)
        if not dry_run:
            atomic_write_text(path, rendered)
        return ManagedWriteResult(
            path=path,
            action="updated",
            backup_path=backup_path,
            changed=True,
        )

    if not dry_run:
        atomic_write_text(path, rendered)
    return ManagedWriteResult(path=path, action="created", changed=True)


def upsert_managed_block(
    path: Path,
    *,
    block_name: str,
    content: str,
    comment_prefix: str = "#",
    dry_run: bool = False,
) -> ManagedWriteResult:
    start_marker = f"{comment_prefix} BEGIN {MANAGED_MARKER}:{block_name}"
    end_marker = f"{comment_prefix} END {MANAGED_MARKER}:{block_name}"
    block = f"{start_marker}\n{content.rstrip()}\n{end_marker}\n"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    if start_marker in existing and end_marker in existing:
        before, _, rest = existing.partition(start_marker)
        _, _, after = rest.partition(end_marker)
        updated = f"{before}{block}{after.lstrip()}"
        action = "updated"
    else:
        prefix = "" if not existing or existing.endswith("\n") else "\n"
        updated = f"{existing}{prefix}{block}"
        action = "created" if not existing else "updated"

    if existing == updated:
        return ManagedWriteResult(path=path, action="unchanged", changed=False)

    backup_path = backup_file(path) if path.exists() and not dry_run else None
    if not dry_run:
        atomic_write_text(path, updated)
    return ManagedWriteResult(path=path, action=action, backup_path=backup_path, changed=True)


def remove_managed_block(
    path: Path,
    *,
    block_name: str,
    comment_prefix: str = "#",
    dry_run: bool = False,
) -> ManagedWriteResult:
    if not path.exists():
        return ManagedWriteResult(path=path, action="missing", changed=False)

    start_marker = f"{comment_prefix} BEGIN {MANAGED_MARKER}:{block_name}"
    end_marker = f"{comment_prefix} END {MANAGED_MARKER}:{block_name}"
    existing = path.read_text(encoding="utf-8")
    if start_marker not in existing or end_marker not in existing:
        return ManagedWriteResult(path=path, action="unchanged", changed=False)

    before, _, rest = existing.partition(start_marker)
    _, _, after = rest.partition(end_marker)
    updated = f"{before.rstrip()}\n{after.lstrip()}".rstrip() + "\n"
    backup_path = None if dry_run else backup_file(path)
    if not dry_run:
        atomic_write_text(path, updated)
    return ManagedWriteResult(path=path, action="updated", backup_path=backup_path, changed=True)


def remove_managed_file(path: Path, *, dry_run: bool = False) -> ManagedWriteResult:
    if not path.exists():
        return ManagedWriteResult(path=path, action="missing", changed=False)
    if not is_managed_file(path):
        return ManagedWriteResult(path=path, action="skipped", changed=False)
    backup_path = None if dry_run else backup_file(path)
    if not dry_run:
        path.unlink(missing_ok=True)
    return ManagedWriteResult(path=path, action="removed", backup_path=backup_path, changed=True)
