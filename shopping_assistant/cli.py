"""
CLI entrypoint for the conversational shopping assistant.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import Iterator, Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from .clarifier import ClarificationEngine, ClarificationState
from .config import get_settings
from .llm import LLMClient
from .research import ProductRecommendation, ResearchAgent

app = typer.Typer(add_completion=False, help="Conversational shopping assistant.")
console = Console()


@contextmanager
def _llm_status(message: str) -> Iterator[None]:
    with console.status(message, spinner="dots", spinner_style="magenta"):
        yield


def _handle_clarification(
    topic: str, clarifier: ClarificationEngine
) -> ClarificationState:
    """
    Run the clarification interview loop.
    """

    state = ClarificationState(topic=topic)
    console.print()
    console.print(
        Panel.fit(
            "Great! I'll ask a few quick questions so I can tailor the search.",
            title="Clarify Needs",
            border_style="cyan",
        )
    )

    while True:
        with _llm_status("[bold magenta]Thinking about the next question...[/]"):
            question = clarifier.next_question(state)
        if question is None:
            break

        console.print(f"[bold cyan]?[/] {question}")
        answer = Prompt.ask("You", default="", show_default=False)
        normalized = answer.strip().lower()

        if normalized in {"done", "that's enough", "no"}:
            console.print("[yellow]Understood. I'll work with what I have.[/]")
            state.complete = True
            break

        if not answer.strip() or normalized in {"skip", "not sure", "pass"}:
            console.print("[yellow]Skipping — I'll try a different angle.[/]")
            state.add_turn(question, "User skipped this question.")
            continue

        state.add_turn(question, answer.strip())

    if not state.summary:
        # Fallback summary based on collected answers.
        bullet_lines = [f"- {turn.question}: {turn.answer}" for turn in state.turns]
        state.summary = "\n".join(bullet_lines) if bullet_lines else topic

    console.print()
    console.print(
        Panel(
            state.summary,
            title="What I heard",
            border_style="cyan",
        )
    )

    return state


def _render_recommendations(
    recommendations: list[ProductRecommendation], comparison: str
) -> None:
    """
    Pretty-print the recommendation set.
    """

    console.print()
    console.print(
        Panel.fit(
            "Here are the standout options I found.",
            title="Recommendations",
            border_style="green",
        )
    )

    for idx, rec in enumerate(recommendations, start=1):
        body_lines = [
            f"[link={rec.url}]{rec.name}[/link]",
            "",
            rec.why_it_fits,
            "",
            "[bold green]Highlights[/]:",
        ]
        body_lines.extend(f"- {item}" for item in rec.highlights if item)
        if rec.watchouts:
            body_lines.append("")
            body_lines.append("[bold yellow]Watch-outs[/]:")
            body_lines.extend(f"- {item}" for item in rec.watchouts if item)
        if rec.best_for:
            body_lines.append("")
            body_lines.append(f"[italic]Best for:[/] {rec.best_for}")

        console.print(
            Panel(
                "\n".join(body_lines),
                title=f"Option {idx}",
                subtitle=rec.url,
                border_style="green",
            )
        )

    if comparison:
        console.print(Markdown(f"**Quick comparison tip:** {comparison}"))


@app.command("chat")
def run_chat(
    product: Optional[str] = typer.Option(None, "--product", "-p", help="What you want to buy.")
) -> None:
    """
    Launch the interactive conversation.
    """

    try:
        settings = get_settings()
    except RuntimeError as exc:
        typer.echo(f"[Configuration error] {exc}", err=True)
        raise typer.Exit(code=1) from exc

    llm = LLMClient(settings)
    clarifier = ClarificationEngine(llm, settings)

    console.print(
        Panel.fit(
            "Hi! I'm your personal shopping sidekick. What are we shopping for today?",
            title="Shopping Assistant",
            border_style="magenta",
        )
    )

    if not product:
        product = Prompt.ask("You", default="").strip()

    if not product:
        console.print("[red]I need a product or category to get started.[/]")
        raise typer.Exit(code=0)

    research_agent: ResearchAgent
    try:
        research_agent = ResearchAgent(llm, settings)
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=1) from exc

    clarification_state = _handle_clarification(product, clarifier)

    console.print()
    console.print(
        Panel.fit(
            "Let me search the web for the best matches...",
            title="Research",
            border_style="blue",
        )
    )

    try:
        with _llm_status("[bold blue]Drafting smart search queries...[/]"):
            queries = research_agent.craft_search_queries(
                clarification_state.topic, clarification_state.summary or ""
            )
        with _llm_status("[bold blue]Gathering fresh product listings...[/]"):
            research = research_agent.collect_research(queries)
        with _llm_status("[bold blue]Comparing options for best value...[/]"):
            result = research_agent.recommend_products(
                clarification_state.topic,
                clarification_state.summary or "",
                research,
            )
    except Exception as exc:  # noqa: BLE001 - surfaced directly to CLI
        console.print(f"[red]Search or recommendation failed: {exc}[/]")
        raise typer.Exit(code=1) from exc

    recommendations: list[ProductRecommendation] = result.get("recommendations", [])
    comparison: str = result.get("comparison_insight", "")
    discarded: int = int(result.get("discarded_count") or 0)
    if not recommendations:
        console.print("[yellow]I couldn't assemble confident recommendations this time.[/]")
        raise typer.Exit(code=1)

    if discarded:
        console.print(
            f"[yellow]{discarded} suggestion(s) lacked verified product links and were dropped.[/]"
        )

    _render_recommendations(recommendations, comparison)


@app.callback(invoke_without_command=True)
def entrypoint(
    ctx: typer.Context,
    product: Optional[str] = typer.Option(
        None,
        "--product",
        "-p",
        help="What you want to buy. If omitted you'll be prompted.",
    ),
) -> None:
    """
    Allow invoking the assistant without specifying a subcommand.
    """

    if ctx.invoked_subcommand is None:
        ctx.invoke(run_chat, product=product)


def main() -> None:
    """
    Entry point used by `python -m shopping_assistant.cli`.
    """

    try:
        app(prog_name="shopping-assistant")
    except typer.Exit as exit_exc:
        # typer.Exit already handled messaging; just propagate exit code.
        raise SystemExit(exit_exc.exit_code) from exit_exc
    except Exception as exc:  # noqa: BLE001
        typer.echo(f"Unexpected error: {exc}", err=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
