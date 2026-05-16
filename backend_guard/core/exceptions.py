"""Custom exceptions."""

from __future__ import annotations


class BackendGuardError(Exception):
    """Base exception for backend-guard."""


class CommandExecutionError(BackendGuardError):
    """Raised when a subprocess command fails unexpectedly."""


class ConfigurationError(BackendGuardError):
    """Raised for invalid or conflicting configuration."""


class FileWriteDeclinedError(BackendGuardError):
    """Raised when a write would overwrite an unmanaged file without approval."""
