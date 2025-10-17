from __future__ import annotations

from pathlib import Path

from git import Actor, Repo

from pivot.config import RepositoryConfig
from pivot.pipeline import LocalizationPipeline

AUTHOR = Actor("Pivot Bot", "pivot@example.com")


def _init_origin(path: Path) -> Repo:
    origin = Repo.init(path)
    docs_dir = path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    readme = docs_dir / "readme.md"
    readme.write_text("hello", encoding="utf-8")
    origin.index.add([str(readme.relative_to(path))])
    origin.index.commit("init", author=AUTHOR, committer=AUTHOR)
    origin.git.branch("-M", "main")
    return origin


def test_pipeline_collects_and_records_changes(tmp_path: Path) -> None:
    origin = _init_origin(tmp_path / "origin")
    config = RepositoryConfig(
        name="sample",
        url=str(origin.working_tree_dir),
        branch="main",
        docs_path=Path("docs"),
    )

    pipeline = LocalizationPipeline(tmp_path / "work")

    plans = pipeline.collect([config])
    assert len(plans) == 1
    plan = plans[0]
    assert plan.has_changes
    assert plan.pending_files == [Path("docs/readme.md")]

    pipeline.mark_processed(plan)
    plans = pipeline.collect([config])
    assert plans[0].pending_files == []

    new_doc = Path(origin.working_tree_dir) / "docs" / "usage.yaml"
    new_doc.write_text("key: value", encoding="utf-8")
    origin.index.add([str(new_doc.relative_to(origin.working_tree_dir))])
    origin.index.commit("add usage", author=AUTHOR, committer=AUTHOR)

    plans = pipeline.collect([config])
    updated_plan = plans[0]
    assert updated_plan.pending_files == [Path("docs/usage.yaml")]
    assert updated_plan.has_changes
