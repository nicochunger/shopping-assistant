"""
Utilities for interacting with OpenAI models.
"""

from __future__ import annotations

import json
from textwrap import dedent
from typing import Any, Dict, List, Sequence

from openai import OpenAI

from .config import Settings


class LLMClient:
    """
    Thin wrapper around the OpenAI Chat Completions API to simplify structured prompts.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)

    @property
    def model(self) -> str:
        return self._settings.openai_model

    def generate(
        self,
        system_prompt: str,
        messages: Sequence[Dict[str, Any]],
        *,
        temperature: float | None = None,
    ) -> str:
        """
        Call the OpenAI chat completions API and return the generated text.
        """

        input_messages: List[Dict[str, Any]] = [
            {"role": "system", "content": dedent(system_prompt).strip()}
        ]
        input_messages.extend(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": input_messages,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature

        response = self._client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content
        if isinstance(content, list):
            text = "".join(
                part.text for part in content if getattr(part, "type", "") == "text"
            )
        else:
            text = content or ""

        return text.strip()

    def generate_json(
        self,
        system_prompt: str,
        messages: Sequence[Dict[str, Any]],
        *,
        temperature: float | None = None,
    ) -> Dict[str, Any]:
        """
        Request a JSON response and parse it into a dictionary.
        """

        raw = self.generate(system_prompt, messages, temperature=temperature)
        try:
            return json.loads(self._strip_code_fence(raw))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "The language model returned an invalid JSON payload:\n"
                f"{raw}"
            ) from exc

    @staticmethod
    def _strip_code_fence(text: str) -> str:
        """
        Remove Markdown code fences if present.
        """

        stripped = text.strip()
        if stripped.startswith("```"):
            # Handle ```json\n...\n``` style responses from models.
            stripped = stripped.split("\n", 1)[-1]
            if stripped.endswith("```"):
                stripped = stripped.rsplit("\n", 1)[0]
        return stripped.strip()
