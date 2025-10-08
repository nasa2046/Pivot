"""Configuration loading and validation utilities for Pivot."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)
from ruamel.yaml import YAML

DEFAULT_CONFIG_FILENAMES: tuple[str, ...] = (
    "pivot.yaml",
    "pivot.yml",
    "config/pivot.yaml",
    "config/pivot.yml",
)


class ConfigError(RuntimeError):
    """Raised when configuration loading or validation fails."""


class TranslationProviderConfig(BaseModel):
    """Settings for the translation provider backend."""

    provider: str = Field(description="Provider identifier, e.g. 'openai'.")
    model: str = Field(description="Model name to request, e.g. 'gpt-4'.")
    base_url: AnyHttpUrl | None = Field(
        default=None,
        description="Optional base URL for the provider API.",
    )
    api_key: SecretStr | None = Field(
        default=None,
        description="API key supplied directly in the configuration.",
    )
    api_key_env: str | None = Field(
        default=None,
        description="Environment variable that stores the API key.",
    )
    timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        description="Request timeout in seconds for translation calls.",
    )

    @model_validator(mode="after")
    def _check_api_key_source(self) -> TranslationProviderConfig:
        if not self.api_key and not self.api_key_env:
            msg = "translation.api_key 或 translation.api_key_env 至少需提供一个"
            raise ConfigError(msg)
        return self

    def resolve_api_key(self) -> SecretStr:
        """Return the API key, preferring inline value then environment variable."""

        if self.api_key:
            return self.api_key
        assert self.api_key_env  # for mypy
        value = os.getenv(self.api_key_env)
        if value:
            return SecretStr(value)
        msg = f"环境变量 {self.api_key_env!r} 未设置或为空"
        raise ConfigError(msg)


class RepositoryConfig(BaseModel):
    """Settings for a repository to monitor and translate."""

    name: str = Field(description="Local identifier for the repository.")
    url: str = Field(description="Git clone URL for the repository.")
    branch: str = Field(default="main", description="Default branch to track.")
    docs_path: Path = Field(
        default=Path("."),
        description="Relative path in the repo containing documentation roots.",
    )

    @field_validator("docs_path", mode="before")
    @classmethod
    def _make_path(cls, value: object) -> Path:
        if isinstance(value, Path):
            return value
        return Path(str(value))


class AppConfig(BaseModel):
    """Top-level application configuration."""

    work_dir: Path = Field(description="Directory used to store state and cache data.")
    output_dir: Path = Field(description="Directory where translated files are emitted.")
    repositories: list[RepositoryConfig] = Field(default_factory=list)
    translation: TranslationProviderConfig

    @field_validator("work_dir", "output_dir", mode="before")
    @classmethod
    def _expand_path(cls, value: object) -> Path:
        raw = Path(str(value)).expanduser()
        return Path(os.path.expandvars(str(raw)))

    @model_validator(mode="after")
    def _ensure_repositories(self) -> AppConfig:
        if not self.repositories:
            msg = "必须至少配置一个 repositories 条目"
            raise ConfigError(msg)
        return self

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""

        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


def _read_yaml(path: Path) -> dict[str, Any]:
    yaml = YAML(typ="safe")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.load(fh) or {}
    if not isinstance(data, dict):
        msg = f"配置文件 {path} 顶层结构必须是字典"
        raise ConfigError(msg)
    return dict(data)


def _candidate_paths() -> Iterable[Path]:
    env_override = os.getenv("PIVOT_CONFIG")
    if env_override:
        yield Path(env_override)
    cwd = Path.cwd()
    for name in DEFAULT_CONFIG_FILENAMES:
        yield cwd / name


def discover_config_path(explicit: Path | None = None) -> Path:
    """Find the configuration file to use."""

    if explicit:
        path = explicit.expanduser()
        if not path.exists():
            msg = f"指定的配置文件 {path} 不存在"
            raise ConfigError(msg)
        return path

    for candidate in _candidate_paths():
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded

    msg = "未能找到默认配置文件，请使用 --config 指定或设置 PIVOT_CONFIG"
    raise ConfigError(msg)


def load_config(path: Path | None = None) -> AppConfig:
    """Load and validate the application configuration."""

    config_path = discover_config_path(path)
    try:
        raw_data = _read_yaml(config_path)
        config = AppConfig.model_validate(raw_data)
    except ValidationError as exc:
        raise ConfigError(str(exc)) from exc
    except ConfigError:
        raise
    except OSError as exc:  # pragma: no cover - filesystem faults are rare
        raise ConfigError(f"读取配置文件 {config_path} 失败: {exc}") from exc

    return config


__all__ = [
    "AppConfig",
    "ConfigError",
    "RepositoryConfig",
    "TranslationProviderConfig",
    "discover_config_path",
    "load_config",
]
