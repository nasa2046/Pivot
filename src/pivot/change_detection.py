"""Detect repository documentation changes."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from git import Repo

from pivot.config import RepositoryConfig
from pivot.state import RepositoryState, StateStore

DEFAULT_TRACKED_SUFFIXES: tuple[str, ...] = (".md", ".markdown", ".yaml", ".yml")


class ChangeDetector:
    """Identify documentation files that have changed since the last run."""

    def __init__(
        self,
        state_store: StateStore,
        tracked_suffixes: Sequence[str] = DEFAULT_TRACKED_SUFFIXES,
    ) -> None:
        self.state_store = state_store
        self._tracked_suffixes = tuple(s.lower() for s in tracked_suffixes)

    def collect_changes(self, config: RepositoryConfig, repo: Repo) -> list[Path]:
        state = self.state_store.get_repository_state(config.name)
        head_commit = repo.head.commit.hexsha

        if state.last_synced_commit == head_commit:
            return []

        candidates = self._candidate_paths(repo, state)
        filtered = [path for path in candidates if self._is_translatable(path, config.docs_path)]
        return filtered

    def record_processed(self, config: RepositoryConfig, repo: Repo) -> None:
        state = RepositoryState(last_synced_commit=repo.head.commit.hexsha)
        self.state_store.set_repository_state(config.name, state)

    def _candidate_paths(self, repo: Repo, state: RepositoryState) -> list[Path]:
        if state.last_synced_commit:
            diff = repo.git.diff(f"{state.last_synced_commit}..HEAD", "--name-only")
            return [Path(line.strip()) for line in diff.splitlines() if line.strip()]

        files = repo.git.ls_files()
        return [Path(line.strip()) for line in files.splitlines() if line.strip()]

    def _is_translatable(self, path: Path, docs_root: Path) -> bool:
        suffix = path.suffix.lower()
        if suffix not in self._tracked_suffixes:
            return False
        if docs_root in (Path("."), Path("")):
            return True
        try:
            path.relative_to(docs_root)
        except ValueError:
            return False
        return True


__all__ = ["ChangeDetector", "DEFAULT_TRACKED_SUFFIXES"]
