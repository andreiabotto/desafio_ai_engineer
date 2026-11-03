"""Interface CLI do agente Empório da Música."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from emporio_agent.agent.graph import AgentAPIError, run_agent_turn
from emporio_agent.agent.memory import ConversationMemory
from emporio_agent.bootstrap import bootstrap_agent, ensure_data_ready

app = typer.Typer(add_completion=False, no_args_is_help=False, invoke_without_command=True)
console = Console()

_HELP = """
Comandos:
  /nova   — limpa o histórico
  /sair   — encerra
  /help   — esta ajuda
""".strip()


def _format_api_error(exc: BaseException) -> str:
    kind = getattr(exc, "kind", "unknown") if isinstance(exc, AgentAPIError) else "unknown"
    base = f"[red]Erro ao consultar o modelo/API:[/red] {exc}"
    if kind == "rate_limit":
        return (
            f"{base}\n"
            "[dim]Rate limit / TPM do Groq: aguarde uns segundos, use /nova "
            "para limpar o histórico, ou tente de novo.[/dim]"
        )
    if kind == "auth":
        return f"{base}\n[dim]Verifique GROQ_API_KEY no arquivo .env.[/dim]"
    if kind == "context":
        return f"{base}\n[dim]Contexto longo demais — use /nova e tente uma pergunta mais curta.[/dim]"
    return f"{base}\n[dim]Se persistir, confira rede, .env e logs com --verbose.[/dim]"


def run_chat(verbose: bool = False, reingest: bool = False) -> None:
    try:
        agent, settings = bootstrap_agent(
            force=reingest,
            log=lambda msg: console.print(f"[cyan]{msg}[/cyan]"),
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Falha ao iniciar o agente:[/red] {exc}")
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
        except Exception as exc:  # noqa: BLE001
            console.print(_format_api_error(exc))


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
    app_path = Path(__file__).resolve().parent / "ui" / "app.py"
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
    ensure_data_ready(
        force=force,
        log=lambda msg: console.print(f"[cyan]{msg}[/cyan]"),
        load_embeddings=False,
    )
    console.print("[green]Ingestão concluída.[/green]")


if __name__ == "__main__":
    app()
