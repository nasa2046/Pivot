"""Command line interface for Pivot."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from pivot import get_version
from pivot.config import AppConfig, ConfigError, load_config

console = Console()

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Pivot - GitHub 文档持续本地化工具",
)


def _print_config_summary(config: AppConfig) -> None:
    table = Table(title="已加载的仓库配置")
    table.add_column("名称", style="cyan")
    table.add_column("URL", style="magenta")
    table.add_column("分支", style="green")
    table.add_column("文档路径", style="yellow")

    for repo in config.repositories:
        table.add_row(repo.name, repo.url, repo.branch, str(repo.docs_path))

    console.print(table)
    console.print(f"状态缓存目录: [bold]{config.work_dir}[/bold]")
    console.print(f"译文输出目录: [bold]{config.output_dir}[/bold]")


def _load_or_exit(config_path: Path | None) -> AppConfig:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        console.print(f"[red]配置加载失败：{exc}[/red]")
        raise typer.Exit(code=1) from exc
    return config


@app.callback()
def default(  # pragma: no cover - Typer callback integration
    version: bool = typer.Option(  # noqa: FBT001
        False,
        "--version",
        help="显示当前版本",
        callback=lambda value: _show_version_and_exit(value),
        is_eager=True,
    )
) -> None:
    """Base callback for shared options."""


def _show_version_and_exit(value: bool) -> None:
    if value:
        console.print(f"Pivot {get_version()}")
        raise typer.Exit()


@app.command("validate-config")
def validate_config(  # noqa: D401
    config: Path | None = typer.Option(  # noqa: FBT001
        None,
        "--config",
        "-c",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="指定配置文件路径",
    )
) -> None:
    """验证配置文件是否有效。"""

    app_config = _load_or_exit(config)
    console.print("[green]配置加载成功！[/green]")
    _print_config_summary(app_config)


@app.command()
def run(  # noqa: D401
    config: Path | None = typer.Option(  # noqa: FBT001
        None,
        "--config",
        "-c",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        resolve_path=True,
        help="指定配置文件路径",
    ),
    dry_run: bool = typer.Option(  # noqa: FBT001
        True,
        "--dry-run/--execute",
        help="默认只演示流程，不执行实际的翻译调度。",
    ),
) -> None:
    """运行翻译流水线（当前为占位实现）。"""

    app_config = _load_or_exit(config)
    app_config.ensure_directories()
    console.print("[green]配置加载成功，目录已就绪。[/green]")
    _print_config_summary(app_config)

    if dry_run:
        console.print(
            "[yellow]当前处于 dry-run 模式。翻译流水线将在后续迭代中实现。[/yellow]"
        )
    else:  # pragma: no cover - 流水线待实现
        console.print("[red]执行模式尚未实现。[/red]")


def main() -> None:  # pragma: no cover - 控制台入口
    app()


__all__ = ["app", "main"]
