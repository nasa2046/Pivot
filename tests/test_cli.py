from __future__ import annotations

import textwrap
from pathlib import Path

from git import Actor, Repo
from typer.testing import CliRunner

from pivot.cli import app

runner = CliRunner()

AUTHOR = Actor("Pivot Bot", "pivot@example.com")


def _init_origin(path: Path) -> Repo:
    origin = Repo.init(path)
    docs_dir = path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    readme = docs_dir / "readme.md"
    readme.write_text("# Intro\n\nhello\n", encoding="utf-8")
    origin.index.add([str(readme.relative_to(path))])
    origin.index.commit("init", author=AUTHOR, committer=AUTHOR)
    origin.git.branch("-M", "main")
    return origin


def _write_config(
    tmp_path: Path,
    *,
    repo_url: str,
    work_dir: Path,
    output_dir: Path,
) -> Path:
    config_path = tmp_path / "pivot.yaml"
    config = textwrap.dedent(
        f"""
        work_dir: {work_dir}
        output_dir: {output_dir}
        repositories:
          - name: repo
            url: {repo_url}
            branch: main
            docs_path: docs
        translation:
          provider: mock
          model: tiny
          api_key: dummy
        """
    ).strip()
    config_path.write_text(config + "\n", encoding="utf-8")
    return config_path


def test_validate_config_command(tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path,
        repo_url="https://github.com/example/repo",
        work_dir=tmp_path / "cache",
        output_dir=tmp_path / "output",
    )
    result = runner.invoke(app, ["validate-config", "--config", str(config_path)])
    assert result.exit_code == 0, result.stdout
    assert "配置加载成功" in result.stdout


def test_run_dry_run(tmp_path: Path) -> None:
    origin_path = tmp_path / "origin"
    _init_origin(origin_path)

    config_path = _write_config(
        tmp_path,
        repo_url=str(origin_path),
        work_dir=tmp_path / "work",
        output_dir=tmp_path / "out",
    )
    result = runner.invoke(app, ["run", "--config", str(config_path)])
    assert result.exit_code == 0, result.stdout
    assert "dry-run" in result.stdout
    assert "docs/readme.md" in result.stdout
