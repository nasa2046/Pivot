from __future__ import annotations

import textwrap
from pathlib import Path

from typer.testing import CliRunner

from pivot.cli import app

runner = CliRunner()


def _write_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "pivot.yaml"
    config = textwrap.dedent(
        """
        work_dir: ./cache
        output_dir: ./output
        repositories:
          - name: repo
            url: https://github.com/example/repo
        translation:
          provider: mock
          model: tiny
          api_key: dummy
        """
    ).strip()
    config_path.write_text(config + "\n", encoding="utf-8")
    return config_path


def test_validate_config_command(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    result = runner.invoke(app, ["validate-config", "--config", str(config_path)])
    assert result.exit_code == 0, result.stdout
    assert "配置加载成功" in result.stdout


def test_run_dry_run(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path)
    result = runner.invoke(app, ["run", "--config", str(config_path)])
    assert result.exit_code == 0, result.stdout
    assert "dry-run" in result.stdout
