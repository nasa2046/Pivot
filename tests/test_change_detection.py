from __future__ import annotations

from pathlib import Path

from git import Actor, Repo

from pivot.change_detection import ChangeDetector
from pivot.config import RepositoryConfig
from pivot.repository import RepositoryManager
from pivot.state import StateStore

AUTHOR = Actor("Pivot Bot", "pivot@example.com")


def _init_origin(path: Path) -> Repo:
    origin = Repo.init(path)
    docs_dir = path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "readme.md").write_text("hello", encoding="utf-8")
    (path / "code.py").write_text("print('hi')", encoding="utf-8")
    origin.index.add(["docs/readme.md", "code.py"])
    origin.index.commit("init", author=AUTHOR, committer=AUTHOR)
    origin.git.branch("-M", "main")
    return origin


def test_change_detector_tracks_updates(tmp_path: Path) -> None:
    origin_path = tmp_path / "origin"
    origin = _init_origin(origin_path)

    manager = RepositoryManager(tmp_path / "repos")
    config = RepositoryConfig(
        name="sample",
        url=str(origin_path),
        branch="main",
        docs_path=Path("docs"),
    )
    repo = manager.sync(config)

    state_store = StateStore(tmp_path / "state" / "repositories.json")
    detector = ChangeDetector(state_store)

    initial_changes = detector.collect_changes(config, repo)
    assert Path("docs/readme.md") in initial_changes
    assert all(path.suffix in {".md", ".yaml", ".yml", ".markdown"} for path in initial_changes)

    detector.record_processed(config, repo)
    assert detector.collect_changes(config, repo) == []

    new_doc = origin_path / "docs" / "usage.yaml"
    new_doc.write_text("key: value", encoding="utf-8")
    origin.index.add(["docs/usage.yaml"])
    origin.index.commit("add usage", author=AUTHOR, committer=AUTHOR)

    manager.sync(config)
    updated_changes = detector.collect_changes(config, repo)
    assert Path("docs/usage.yaml") in updated_changes

    detector.record_processed(config, repo)
