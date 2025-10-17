"""High-level orchestration utilities for the Pivot localization pipeline."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from git import Repo

from pivot.change_detection import ChangeDetector
from pivot.config import RepositoryConfig
from pivot.repository import RepositoryManager
from pivot.state import StateStore


@dataclass(slots=True)
class RepositoryPlan:
    """Aggregated information about a repository run."""

    config: RepositoryConfig
    repo: Repo
    pending_files: list[Path] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Whether the repository contains documents requiring translation."""

        return bool(self.pending_files)


class LocalizationPipeline:
    """Coordinate repository synchronization and change detection."""

    def __init__(
        self,
        work_dir: Path,
        *,
        repository_manager: RepositoryManager | None = None,
        state_store: StateStore | None = None,
        change_detector: ChangeDetector | None = None,
    ) -> None:
        self.work_dir = work_dir
        self._repos_dir = work_dir / "repositories"
        self._state_file = work_dir / "state" / "repositories.json"

        self.repository_manager = repository_manager or RepositoryManager(self._repos_dir)
        self.state_store = state_store or StateStore(self._state_file)
        self.change_detector = change_detector or ChangeDetector(self.state_store)

    def collect(self, configs: Sequence[RepositoryConfig]) -> list[RepositoryPlan]:
        """Synchronize repositories and gather pending document changes."""

        plans: list[RepositoryPlan] = []
        for config in configs:
            repo = self.repository_manager.sync(config)
            raw_changes = self.change_detector.collect_changes(config, repo)
            pending = self._deduplicate(raw_changes)
            plans.append(RepositoryPlan(config=config, repo=repo, pending_files=pending))
        return plans

    def mark_processed(self, plan: RepositoryPlan) -> None:
        """Persist that the given plan has been processed."""

        self.change_detector.record_processed(plan.config, plan.repo)

    def mark_all_processed(self, plans: Sequence[RepositoryPlan]) -> None:
        """Persist that all provided plans have been processed."""

        for plan in plans:
            self.mark_processed(plan)

    @staticmethod
    def _deduplicate(paths: Sequence[Path]) -> list[Path]:
        ordered: OrderedDict[Path, None] = OrderedDict()
        for path in paths:
            ordered[Path(path)] = None
        return list(ordered.keys())


__all__ = ["LocalizationPipeline", "RepositoryPlan"]
