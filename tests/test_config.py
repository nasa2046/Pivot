from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from pivot.config import ConfigError, TranslationProviderConfig, load_config


def _write_config(path: Path, content: str) -> Path:
    text = textwrap.dedent(content).strip()
    path.write_text(text + "\n", encoding="utf-8")
    return path


def test_load_config_from_explicit_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PIVOT_TEST_KEY", "secret")
    config_path = _write_config(
        tmp_path / "pivot.yaml",
        """
        work_dir: ./state
        output_dir: ./output
        repositories:
          - name: sample
            url: https://github.com/example/docs
            branch: main
            docs_path: docs
        translation:
          provider: openai
          model: gpt-4o
          base_url: https://api.openai.com/v1
          api_key_env: PIVOT_TEST_KEY
        """,
    )

    config = load_config(config_path)

    assert config.work_dir == Path("./state")
    assert config.output_dir == Path("./output")
    assert len(config.repositories) == 1
    repo = config.repositories[0]
    assert repo.name == "sample"
    assert repo.branch == "main"
    assert repo.docs_path == Path("docs")
    assert config.translation.resolve_api_key().get_secret_value() == "secret"


def test_translation_provider_requires_api_key() -> None:
    with pytest.raises(ConfigError):
        TranslationProviderConfig(provider="mock", model="x")


def test_missing_config_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError):
        load_config()


def test_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    config_path = _write_config(
        tmp_path / "custom.yaml",
        """
        work_dir: ./cache
        output_dir: ./out
        repositories:
          - name: sample
            url: https://github.com/example/repo
        translation:
          provider: mock
          model: m1
          api_key: dummy
        """,
    )

    monkeypatch.setenv("PIVOT_CONFIG", str(config_path))
    config = load_config()
    assert config.work_dir == Path("./cache")
    assert config.translation.resolve_api_key().get_secret_value() == "dummy"

    monkeypatch.delenv("PIVOT_CONFIG")
