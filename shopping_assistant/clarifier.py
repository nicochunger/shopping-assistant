"""
Clarification stage that gathers the shopper's needs before researching products.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from .config import Settings
from .llm import LLMClient


@dataclass
class ClarificationTurn:
    """
    A record of one question/answer pair captured during clarification.
    """

    question: str
    answer: str


@dataclass
class ClarificationState:
    """
    Tracks conversation progress during the clarification stage.
    """

    topic: str
    turns: List[ClarificationTurn] = field(default_factory=list)
    summary: str | None = None
    complete: bool = False

    @property
    def answers(self) -> Sequence[str]:
        return [turn.answer for turn in self.turns]

    @property
    def questions(self) -> Sequence[str]:
        return [turn.question for turn in self.turns]

    def add_turn(self, question: str, answer: str) -> None:
        self.turns.append(ClarificationTurn(question=question, answer=answer))


class ClarificationEngine:
    """
    Uses an LLM to iteratively ask targeted questions until the shopper's needs are clear.
    """

    SYSTEM_PROMPT = """
        You are a personable but efficient shopping assistant.
        Your job is to understand a shopper's true needs before suggesting products.
        Ask one targeted follow-up question at a time. Reference what you already know.
        Avoid repeating previous questions.

        Respond strictly as JSON with the following schema:
        {
          "question": string | null,
          "should_continue": boolean,
          "updated_summary": string,
          "rationale": string
        }
        - "question" should be null when "should_continue" is false.
        - "updated_summary" must be a concise bullet-style narrative of what you know.
        - Do not include markdown code fences.
    """

    def __init__(self, llm: LLMClient, settings: Settings) -> None:
        self._llm = llm
        self._settings = settings

    def next_question(self, state: ClarificationState) -> str | None:
        """
        Ask the model for the next question to pose to the shopper.
        Returns None when clarification is complete.
        """

        if state.complete:
            return None

        if len(state.turns) >= self._settings.clarification_question_limit:
            state.complete = True
            return None

        user_content = self._build_user_prompt(state)
        result = self._llm.generate_json(
            self.SYSTEM_PROMPT,
            [{"role": "user", "content": user_content}],
        )

        state.summary = result.get("updated_summary", state.summary)
        should_continue = bool(result.get("should_continue", False))
        question = result.get("question")

        if not should_continue or not question:
            state.complete = True
            return None

        return question.strip()

    def _build_user_prompt(self, state: ClarificationState) -> str:
        """
        Assemble the prompt describing conversation progress for the LLM.
        """

        lines = [
            f"Product request: {state.topic}",
            "",
        ]
        if state.turns:
            lines.append("Conversation so far:")
            for turn in state.turns:
                lines.append(f"- Q: {turn.question}")
                lines.append(f"  A: {turn.answer}")
            lines.append("")
        if state.summary:
            lines.append(f"Current summary: {state.summary}")
        lines.append("Decide whether another clarifying question is needed.")
        return "\n".join(lines).strip()
