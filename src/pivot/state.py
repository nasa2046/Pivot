"""State persistence utilities for Pivot."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class StateError(RuntimeError):
    """Raised when state loading or saving fails."""


@dataclass(slots=True)
class RepositoryState:
    """Persisted information about a repository run."""

    last_synced_commit: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> RepositoryState:
        return cls(last_synced_commit=data.get("last_synced_commit"))

    def to_dict(self) -> dict[str, str | None]:
        return {"last_synced_commit": self.last_synced_commit}


class StateStore:
    """Load and persist repository states as JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._states: dict[str, RepositoryState] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            raise StateError(f"无法解析状态文件 {self.path}: {exc}") from exc
        if not isinstance(data, dict):
            raise StateError(f"状态文件 {self.path} 顶层应为字典结构")
        for name, value in data.items():
            if isinstance(value, Mapping):
                self._states[name] = RepositoryState.from_mapping(value)

    def _write(self) -> None:
        serializable = {name: state.to_dict() for name, state in self._states.items()}
        try:
            with self.path.open("w", encoding="utf-8") as fh:
                json.dump(serializable, fh, indent=2, ensure_ascii=False, sort_keys=True)
                fh.write("\n")
        except OSError as exc:  # pragma: no cover - disk failures are rare
            raise StateError(f"写入状态文件 {self.path} 失败: {exc}") from exc

    def get_repository_state(self, name: str) -> RepositoryState:
        return self._states.get(name, RepositoryState())

    def set_repository_state(self, name: str, state: RepositoryState) -> None:
        self._states[name] = state
        self._write()

    def clear(self) -> None:
        self._states.clear()
        if self.path.exists():
            self.path.unlink()


__all__ = ["RepositoryState", "StateError", "StateStore"]
