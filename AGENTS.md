# Repository Guidelines

## Project Structure & Module Organization
The core package lives in `shopping_assistant/` with focused modules: `cli.py` hosts the Typer entrypoint, `clarifier.py` runs the interview loop, `research.py` fetches and ranks products, `llm.py` wraps OpenAI calls, and `config.py` centralizes settings. Keep any new utilities colocated with their domain logic. Project metadata is tracked in `pyproject.toml`, and environment templates live in `.env.example`. Add tests under `tests/` mirroring the package layout (e.g., `tests/test_clarifier.py`).

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local virtualenv.
- `pip install -e .`: install the CLI with editable sources and dependencies.
- `shopping-assistant --product "espresso grinder"`: run the interactive assistant via the installed script.
- `python -m shopping_assistant.cli --product "smart luggage"`: invoke the CLI without installing globally.
- `pytest`: execute the forthcoming test suite; mock Tavily/OpenAI clients to keep runs deterministic.

## Coding Style & Naming Conventions
Use 4-space indentation, type hints, and module-level docstrings as shown in existing code. Favor descriptive snake_case for functions, PascalCase for classes, and prefix async helpers with `async_`. Keep Rich/ Typer console formatting strings centralized in helper functions when reuse is likely. Run `ruff` or `pipx run ruff check .` before committing if you introduce the linter.

## Testing Guidelines
Target pytest-based coverage with `tests/` mirroring module names (`test_llm.py`, etc.). Stub network-bound collaborators (OpenAI, Tavily) via fixtures using `unittest.mock` or `pytest-mock`. When adding new agents or prompts, capture representative user transcripts as fixtures and assert on structured outputs rather than raw strings. Aim for fast, offline test runs that succeed without valid API keys.

## Commit & Pull Request Guidelines
Write commits in imperative mood with concise scope context (`Implement rich panel layout for recommendations`). Reference issues with `Refs #123` when applicable. Pull requests should include: summary of behaviour changes, testing notes (`pytest`/manual CLI), screenshots or transcript snippets for user-facing tweaks, and a checklist of updated docs/config. Request review once lint and tests pass locally.

## Configuration & Secrets
Copy `.env.example` to `.env` for local runs and fill `OPENAI_API_KEY` plus `TAVILY_API_KEY`. Never commit actual secrets; rely on `.gitignore` to keep `.env` private. For integration tests, use fake tokens and disable live research via temporary settings overrides.
