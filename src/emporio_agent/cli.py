"""Interface CLI do agente Empório da Música."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from emporio_agent.agent.graph import build_agent, run_agent_turn
from emporio_agent.agent.memory import ConversationMemory
from emporio_agent.config import get_settings
from emporio_agent.data.ingest_csv import db_ready, ingest_csvs
from emporio_agent.data.ingest_policies import ingest_policies, policies_ready

app = typer.Typer(add_completion=False, no_args_is_help=False, invoke_without_command=True)
console = Console()


def ensure_data_ready(force: bool = False) -> None:
    if force or not db_ready():
        console.print("[cyan]Ingerindo CSVs → SQLite...[/cyan]")
        ingest_csvs()
    if force or not policies_ready():
        console.print(
            "[cyan]Indexando políticas (embeddings locais — pode demorar na 1ª vez)...[/cyan]"
        )
        ingest_policies(force=force)


def run_chat(verbose: bool = False, reingest: bool = False) -> None:
    try:
        ensure_data_ready(force=reingest)
        settings = get_settings()
        agent = build_agent(settings=settings)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Falha ao iniciar o agente:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    memory = ConversationMemory()
    console.print(
        Panel.fit(
            "[bold]Empório da Música[/bold] — Sua música começa aqui.\n"
            "Digite sua mensagem. Comandos: [bold]/nova[/bold], [bold]/sair[/bold]",
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

        try:
            answer, messages = run_agent_turn(
                agent,
                user_text,
                history=memory.as_list(),
                verbose=verbose,
            )
            memory.messages = messages
            console.print()
            console.print(Markdown(answer))
            console.print()
        except Exception as exc:  # noqa: BLE001
            console.print(
                f"[red]Erro ao consultar o modelo/API:[/red] {exc}\n"
                "[dim]Se for rate limit do Groq free tier, aguarde alguns segundos e tente de novo.[/dim]"
            )


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


@app.command("ingest")
def ingest_cmd(
    force: bool = typer.Option(False, "--force", help="Recria SQLite e índice Chroma"),
) -> None:
    """Executa apenas a ingestão de CSVs e políticas."""
    ensure_data_ready(force=force)
    console.print("[green]Ingestão concluída.[/green]")


if __name__ == "__main__":
    app()
