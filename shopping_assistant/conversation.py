"""Conversation helpers for the shopping assistant CLI."""
from __future__ import annotations

from typing import Dict, Any

import json

from .llm import chat_completion
from .config import get_model_catalog

QUESTIONS = [
    ("budget_chf", "What is the maximum budget you want to spend (in CHF)?"),
    ("primary_use", "What is the main use-case for this purchase?"),
    ("constraints", "List any hard constraints (e.g., size, OS compatibility, weight, delivery timing)."),
    ("preference_focus", "Which factors matter most? (e.g., performance, portability, battery, price, sustainability)"),
]


def collect_requirements(memory_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    requirements: Dict[str, Any] = {}
    if memory_snapshot:
        print("Loaded saved preferences (auto-expiring after 90 days):")
        for key, value in memory_snapshot.items():
            print(f"  - {key}: {value}")
        print()
    for key, question in QUESTIONS:
        answer = input(f"{question}\n> ").strip()
        requirements[key] = answer
    return requirements


def summarize_requirements(requirements: Dict[str, Any]) -> str:
    catalog = get_model_catalog()
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Swiss market shopping concierge. Summarize the user's requirements succinctly, "
                "emphasizing CHF budget, Swiss availability, and key tradeoffs."
            ),
        },
        {
            "role": "user",
            "content": "Requirements JSON: " + json.dumps(requirements, ensure_ascii=False),
        },
    ]
    return chat_completion(messages, model=catalog.primary)
