"""OmniMemo CLI — command-line interface for meeting processing."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from omni_memo import __version__
from omni_memo.config import AppConfig
from omni_memo.pipeline import MeetingPipeline

console = Console()


def setup_logging(verbose: bool):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )


@click.group()
@click.version_option(version=__version__, prog_name="omni-memo")
@click.option("--env-file", type=click.Path(), default=None, help="Path to .env file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def main(ctx, env_file, verbose):
    """\u2728 OmniMemo — 多模态会议智能体

    基于 MiMo 全栈模型（Pro + Omni + TTS）的智能会议理解与摘要系统。
    利用 100 万 token 上下文窗口，一次性处理完整会议记录。
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = AppConfig.load(env_file)
    ctx.obj["config"].verbose = verbose
    setup_logging(verbose)


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--title", "-t", default="", help="Meeting title")
@click.option("--voice", is_flag=True, help="Generate voice summary (TTS)")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output directory")
@click.option("--format", "fmt", type=click.Choice(["markdown", "json", "brief"]), default="markdown")
@click.pass_context
def process(ctx, file, title, voice, output, fmt):
    """处理会议文件，生成结构化纪要。

    FILE: 会议记录文本文件路径
    """
    config: AppConfig = ctx.obj["config"]
    issues = config.mimo.validate()
    if issues:
        console.print(f"[red]\u2718 配置错误: {', '.join(issues)}[/red]")
        sys.exit(1)

    pipeline = MeetingPipeline(config)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("正在处理会议...", total=None)
        try:
            result = pipeline.process_file(file, title, voice)
        except Exception as e:
            console.print(f"[red]\u2718 处理失败: {e}[/red]")
            sys.exit(1)
        progress.update(task, description="\u2714 处理完成!")

    # Display results
    console.print()
    if fmt == "brief":
        console.print(Panel(result.minutes.to_brief(), title="会议摘要"))
    elif fmt == "json":
        console.print(result.minutes.to_json())
    else:
        console.print(Panel(result.minutes.to_markdown(), title="会议纪要", border_style="green"))

    # Stats table
    table = Table(title="处理统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")
    table.add_row("会议类型", result.meeting_type.get("type", "unknown"))
    table.add_row("提取段落", str(result.omni_result.total_segments))
    table.add_row("处理分片", str(result.omni_result.chunks_processed))
    table.add_row("使用 1M 上下文", "\u2714 是" if result.omni_result.used_full_context else "\u2718 否")
    table.add_row("总 Token 消耗", f"{result.total_tokens:,}")
    console.print(table)

    # Save
    if output:
        out = Path(output)
    else:
        out = config.output_dir
    pipeline.save_results(result, out)
    console.print(f"\n[dim]输出目录: {out}[/dim]")


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--language", "-l", default="zh", help="Language (zh/en)")
@click.pass_context
def classify(ctx, file, language):
    """识别会议类型。

    FILE: 会议记录文本文件路径
    """
    config: AppConfig = ctx.obj["config"]
    from omni_memo.agent.dispatcher import AgentDispatcher

    text = Path(file).read_text(encoding="utf-8")
    dispatcher = AgentDispatcher(config.mimo)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("正在识别...", total=None)
        result = dispatcher.classify(text[:2000], language)

    console.print(Panel(
        f"类型: [bold]{result.get('type', 'unknown')}[/bold]\n"
        f"置信度: {result.get('confidence', 0):.2f}\n"
        f"理由: {result.get('reason', 'N/A')}",
        title="会议类型识别",
    ))


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--max-tokens", default=800000, help="Max tokens per chunk")
@click.pass_context
def stats(ctx, file, max_tokens):
    """查看文件的 token 统计和分片信息。

    FILE: 文本文件路径
    """
    from omni_memo.utils.chunker import estimate_tokens, chunk_text, should_use_full_context

    text = Path(file).read_text(encoding="utf-8")
    total = estimate_tokens(text)
    use_full = should_use_full_context(text)

    console.print(Panel(
        f"文件: {file}\n"
        f"字符数: {len(text):,}\n"
        f"预估 Token: {total:,}\n"
        f"需要 1M 上下文: {'\u2714 是' if use_full else '\u2718 否'}",
        title="文件统计",
    ))

    if use_full:
        chunks = chunk_text(text, max_tokens=max_tokens)
        table = Table(title="分片详情")
        table.add_column("分片", style="cyan")
        table.add_column("Token", style="green")
        table.add_column("字符范围")
        for c in chunks:
            table.add_row(str(c.index + 1), f"{c.token_estimate:,}", f"{c.char_start}-{c.char_end}")
        console.print(table)


@main.command()
@click.pass_context
def info(ctx):
    """显示 OmniMemo 配置和环境信息。"""
    config: AppConfig = ctx.obj["config"]

    table = Table(title="OmniMemo 配置")
    table.add_column("配置项", style="cyan")
    table.add_column("值", style="green")
    table.add_row("版本", __version__)
    table.add_row("MiMo API Base", config.mimo.api_base)
    table.add_row("API Key", "***" + config.mimo.api_key[-4:] if config.mimo.api_key else "[red]未设置[/red]")
    table.add_row("Omni 模型", config.mimo.model_omni)
    table.add_row("Pro 模型", config.mimo.model_pro)
    table.add_row("TTS 模型", config.mimo.model_tts)
    table.add_row("上下文窗口", f"{config.mimo.max_context_tokens:,} tokens")
    table.add_row("输出目录", str(config.output_dir))
    table.add_row("语言", config.language)
    console.print(table)
