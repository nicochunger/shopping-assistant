"""Ranking assistant using LLM scoring."""
from __future__ import annotations

from typing import Any, Dict, List

from .config import get_model_catalog
from .llm import json_completion


def score_products(requirements: Dict[str, Any], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    catalog = get_model_catalog()
    from json import dumps

    messages = [
        {
            "role": "system",
            "content": (
                "You are a decision analyst helping Swiss shoppers. "
                "Rank only products that were supplied, using Swiss availability and CHF pricing as critical constraints. "
                "Return strictly valid JSON with a `ranked_products` array, including fields: product_id, score, rank, "
                "rationale, price_chf, link, key_specs. Keep rationale under 280 characters."
            ),
        },
        {
            "role": "user",
            "content": (
                "User requirements (JSON):\n" + dumps(requirements, ensure_ascii=False) +
                "\nProducts (JSON):\n" + dumps(products, ensure_ascii=False) +
                "\nOnly return JSON."
            ),
        },
    ]
    data = json_completion(messages, model=catalog.fast)
    ranked = data.get("ranked_products", [])
    return sorted(ranked, key=lambda item: item.get("rank", 999))
