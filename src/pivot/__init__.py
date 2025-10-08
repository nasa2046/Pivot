"""Pivot localization toolkit package."""

from importlib import metadata as _metadata


def get_version() -> str:
    """Return the installed package version."""

    try:
        return _metadata.version("pivot")
    except _metadata.PackageNotFoundError:  # pragma: no cover - during development
        return "0.0.0"


__all__ = ["get_version"]
