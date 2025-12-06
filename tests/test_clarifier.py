"""Tests for the clarification interview flow."""

from __future__ import annotations

from types import SimpleNamespace

from shopping_assistant.clarifier import ClarificationEngine, ClarificationState


class FakeLLM:
    """Minimal stub that returns queued JSON payloads."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests: list[dict] = []

    def generate_json(self, system_prompt, messages):  # noqa: D401 - mimics LLMClient
        self.requests.append({"system": system_prompt, "messages": messages})
        try:
            return self._responses.pop(0)
        except IndexError as exc:  # pragma: no cover - defensive guardrail
            raise AssertionError("LLM called more times than expected") from exc


def test_summary_updates_when_question_limit_is_hit():
    responses = [
        {
            "question": "What's your budget?",
            "should_continue": True,
            "updated_summary": "Working summary",
        },
        {
            "question": None,
            "should_continue": False,
            "updated_summary": "Final summary (under $500)",
        },
    ]
    fake_llm = FakeLLM(responses)
    settings = SimpleNamespace(clarification_question_limit=1)
    clarifier = ClarificationEngine(fake_llm, settings)
    state = ClarificationState(topic="air purifier")

    first_question = clarifier.next_question(state)
    assert first_question == "What's your budget?"
    state.add_turn(first_question, "Under $500")

    next_question = clarifier.next_question(state)
    assert next_question is None
    assert state.complete is True
    assert state.summary == "Final summary (under $500)"

    # Ensure the prompt that hit the limit reminded the model about the cap.
    limit_prompt = fake_llm.requests[-1]["messages"][0]["content"]
    assert "maximum question limit" in limit_prompt
