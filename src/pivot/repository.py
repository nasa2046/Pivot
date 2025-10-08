"""Repository synchronization utilities."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from git import GitCommandError, Repo

from pivot.config import RepositoryConfig


class RepositoryError(RuntimeError):
    """Raised when repository synchronization fails."""


class RepositoryManager:
    """Manage cloning and updating repositories defined in configuration."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def local_path(self, config: RepositoryConfig) -> Path:
        """Return the local path for a repository."""

        return self.base_dir / config.name

    def sync(self, config: RepositoryConfig) -> Repo:
        """Clone or fast-forward the repository to the latest remote state."""

        target_dir = self.local_path(config)
        try:
            if target_dir.exists():
                repo = Repo(target_dir)
                self._fetch_and_update(repo, config)
            else:
                repo = Repo.clone_from(config.url, target_dir, branch=config.branch)
                repo.git.checkout(config.branch)
            return repo
        except GitCommandError as exc:  # pragma: no cover - git errors depend on environment
            raise RepositoryError(f"同步仓库 {config.name} 失败: {exc}") from exc

    def _fetch_and_update(self, repo: Repo, config: RepositoryConfig) -> None:
        repo.remotes.origin.fetch(prune=True)
        repo.git.checkout(config.branch)
        repo.git.pull("origin", config.branch, "--ff-only")

    def sync_all(self, configs: Iterable[RepositoryConfig]) -> dict[str, Repo]:
        """Synchronize all repositories and return mapping by name."""

        result: dict[str, Repo] = {}
        for cfg in configs:
            result[cfg.name] = self.sync(cfg)
        return result


__all__ = ["RepositoryError", "RepositoryManager"]
