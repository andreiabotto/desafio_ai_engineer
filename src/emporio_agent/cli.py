"""Interface CLI do agente Empório da Música."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from emporio_agent.agent.errors import AgentError, map_exception
from emporio_agent.agent.graph import run_agent_turn
from emporio_agent.agent.memory import ConversationMemory
from emporio_agent.bootstrap import bootstrap_agent, ensure_data_ready
from emporio_agent.config import get_settings
from emporio_agent.logging_setup import get_logger, setup_logging

app = typer.Typer(add_completion=False, no_args_is_help=False, invoke_without_command=True)
console = Console()
logger = get_logger(__name__)

_HELP = """
Comandos:
  /nova   — limpa o histórico
  /sair   — encerra
  /help   — esta ajuda
""".strip()


def run_chat(verbose: bool = False, reingest: bool = False) -> None:
    settings = get_settings()
    setup_logging("DEBUG" if verbose else settings.log_level)
    try:
        agent, settings = bootstrap_agent(
            settings=settings,
            force=reingest,
            log=lambda msg: console.print(f"[cyan]{msg}[/cyan]"),
        )
    except Exception as exc:  # noqa: BLE001
        err = map_exception(exc)
        logger.exception("Falha ao iniciar o agente (kind=%s)", err.kind)
        console.print(f"[red]{err.message}[/red]")
        raise typer.Exit(code=1) from exc

    memory = ConversationMemory(max_messages=settings.max_history_messages)
    console.print(
        Panel.fit(
            "[bold]Empório da Música[/bold] — Sua música começa aqui.\n"
            "Digite sua mensagem. Comandos: [bold]/nova[/bold], [bold]/sair[/bold], [bold]/help[/bold]",
            border_style="green",
        )
    )

    while True:
        try:
            user_text = console.input("[bold green]Você>[/bold green] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nAté logo!")
            break

        if not user_text:
            continue
        if user_text.lower() in {"/sair", "/exit", "/quit"}:
            console.print("Até logo! Qualquer coisa é só chamar.")
            break
        if user_text.lower() in {"/nova", "/new", "/reset"}:
            memory.clear()
            console.print("[yellow]Histórico limpo. Nova conversa iniciada.[/yellow]")
            continue
        if user_text.lower() in {"/help", "/ajuda", "?"}:
            console.print(_HELP)
            continue

        try:
            answer, messages = run_agent_turn(
                agent,
                user_text,
                history=memory.as_list(),
                verbose=verbose,
                settings=settings,
            )
            memory.replace_from_turn(messages)
            console.print()
            console.print(Markdown(answer))
            console.print()
        except AgentError as exc:
            logger.warning("Erro no turno (kind=%s)", exc.kind)
            console.print(f"\n[yellow]{exc.message}[/yellow]\n")
        except Exception as exc:  # noqa: BLE001
            err = map_exception(exc)
            logger.exception("Erro inesperado no turno (kind=%s)", err.kind)
            console.print(f"\n[yellow]{err.message}[/yellow]\n")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Mostra tool calls"),
    reingest: bool = typer.Option(False, "--reingest", help="Força reingestão"),
) -> None:
    if ctx.invoked_subcommand is None:
        run_chat(verbose=verbose, reingest=reingest)


@app.command("chat")
def chat_cmd(
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    reingest: bool = typer.Option(False, "--reingest"),
) -> None:
    """Inicia o chat interativo com o agente."""
    run_chat(verbose=verbose, reingest=reingest)


@app.command("ui")
def ui_cmd(
    port: int = typer.Option(8501, "--port", "-p", help="Porta do Streamlit"),
) -> None:
    """Abre a interface gráfica (Streamlit) do chat."""
    setup_logging(get_settings().log_level)
    app_path = Path(__file__).resolve().parent / "ui" / "app.py"
    logger.info("Abrindo UI em http://localhost:%s", port)
    console.print(f"[cyan]Abrindo UI em http://localhost:{port} ...[/cyan]")
    raise SystemExit(
        subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.port",
                str(port),
                "--server.headless",
                "true",
            ]
        )
    )


@app.command("ingest")
def ingest_cmd(
    force: bool = typer.Option(False, "--force", help="Recria SQLite e índice Chroma"),
) -> None:
    """Executa apenas a ingestão de CSVs e políticas."""
    setup_logging(get_settings().log_level)
    ensure_data_ready(
        force=force,
        log=lambda msg: console.print(f"[cyan]{msg}[/cyan]"),
        load_embeddings=False,
    )
    logger.info("Ingestão concluída")
    console.print("[green]Ingestão concluída.[/green]")


if __name__ == "__main__":
    app()
