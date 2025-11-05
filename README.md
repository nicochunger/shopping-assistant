# Shopping Assistant CLI

Conversational command-line agent that guides you from a vague shopping request to confident product recommendations. It first uncovers your true needs through a friendly Q&A, then researches live products using Tavily web search and summarises the best matches with clear reasoning.

## Features
- Clarification interview powered by OpenAI to capture goals, constraints, and preferences.
- Live product research via Tavily Search with LLM-curated search queries.
- Structured recommendations (highlights, watch-outs, best-for) plus a quick comparison tip.
- Configurable defaults for question limits, recommendation count, and model choice.
- Works entirely in the terminal with Rich formatting.

## Prerequisites
- Python 3.10 or later.
- API keys:
  - `OPENAI_API_KEY` for language understanding and generation.
  - `TAVILY_API_KEY` for web search (https://app.tavily.com/).

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Populate an `.env` file (or export environment variables) by copying the template:
```bash
cp .env.example .env
```
Then fill in your actual keys and adjust optional settings as desired.

## Usage
Launch the assistant without any arguments and follow the prompts:
```bash
shopping-assistant
```

Or start with a product category immediately:
```bash
shopping-assistant --product "lightweight travel laptop"
```

Commands can also be run via Python:
```bash
python -m shopping_assistant.cli --product "smart air purifier"
```

During the clarification stage, answer naturally. You can type `skip` to move on or `done` when you feel the assistant has enough context. Once the needs are clear, the agent performs web research, synthesises recommendations, and prints them with purchase links.

## Configuration Reference
- `OPENAI_MODEL`: Defaults to `gpt-4o-mini`. Any Responses API-capable OpenAI model ID works.
- `ASSISTANT_MAX_QUESTIONS`: Hard cap for clarification turns (default `6`).
- `ASSISTANT_RECOMMENDATION_COUNT`: Number of options to surface (default `3`).
- `TAVILY_SEARCH_DEPTH`: `basic` or `advanced` search depth for Tavily (default `advanced`).

## Extending the Agent
- Swap `SearchClient` in `shopping_assistant/research.py` to integrate other search providers.
- Extend the prompts in `clarifier.py` or `research.py` to steer tone or structure.
- Add persistence (e.g., save conversations) by tapping into `ClarificationState` records.

## Troubleshooting
- Missing API keys trigger explicit configuration errors when the CLI starts.
- If the assistant struggles to find strong matches, try broadening the initial request or answering follow-up questions with more detail.
- Network or rate limit issues from Tavily/OpenAI will surface in the Research stage; rerun once connectivity resolves.
