from __future__ import annotations

from pathlib import Path

from git import Actor, Repo

from pivot.config import RepositoryConfig
from pivot.repository import RepositoryManager

AUTHOR = Actor("Pivot Bot", "pivot@example.com")


def _init_origin(path: Path) -> Repo:
    origin = Repo.init(path)
    file_path = path / "docs" / "readme.md"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text("hello", encoding="utf-8")
    origin.index.add([str(file_path.relative_to(path))])
    origin.index.commit("init", author=AUTHOR, committer=AUTHOR)
    origin.git.branch("-M", "main")
    return origin


def test_repository_manager_clone_and_update(tmp_path: Path) -> None:
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
    local_path = manager.local_path(config)
    assert Path(repo.working_tree_dir) == local_path
    initial_head = repo.head.commit.hexsha

    updated_file = origin_path / "docs" / "usage.md"
    updated_file.write_text("usage", encoding="utf-8")
    origin.index.add([str(updated_file.relative_to(origin_path))])
    origin.index.commit("add usage", author=AUTHOR, committer=AUTHOR)

    repo = manager.sync(config)
    assert repo.head.commit.hexsha != initial_head
    assert (local_path / "docs" / "usage.md").exists()
