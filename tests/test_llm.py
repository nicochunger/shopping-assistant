"""Tests for helper utilities in :mod:`shopping_assistant.llm`."""

from shopping_assistant.llm import LLMClient


def test_strip_code_fence_handles_markdown_wrappers():
    raw = """```json\n{"foo": "bar"}\n```"""
    assert LLMClient._strip_code_fence(raw) == '{"foo": "bar"}'


def test_strip_code_fence_returns_plain_text():
    raw = "already json"
    assert LLMClient._strip_code_fence(raw) == "already json"
