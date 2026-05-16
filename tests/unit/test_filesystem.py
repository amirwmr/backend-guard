from __future__ import annotations

from pathlib import Path

from backend_guard.utils.filesystem import remove_managed_file, upsert_managed_block, write_managed_file


def test_write_managed_file_creates_and_updates(tmp_path: Path) -> None:
    target = tmp_path / ".editorconfig"
    created = write_managed_file(target, "root = true")
    updated = write_managed_file(target, "root = false", overwrite=True)

    assert created.action == "created"
    assert updated.action == "updated"
    assert updated.backup_path is not None


def test_write_managed_file_dry_run_does_not_create_backup(tmp_path: Path) -> None:
    target = tmp_path / "ruff.toml"
    target.write_text("# managed-by-backend-guard\nold = true\n", encoding="utf-8")
    result = write_managed_file(target, "old = false", dry_run=True)
    assert result.backup_path is None
    assert "old = true" in target.read_text(encoding="utf-8")


def test_upsert_and_remove_managed_block(tmp_path: Path) -> None:
    target = tmp_path / ".gitignore"
    upsert_managed_block(target, block_name="gitignore", content=".venv/")
    remove_result = remove_managed_file(tmp_path / "nonexistent")
    content = target.read_text(encoding="utf-8")

    assert "BEGIN managed-by-backend-guard:gitignore" in content
    assert remove_result.action == "missing"
