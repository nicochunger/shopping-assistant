"""Entry point for the Buy-with-Me shopping assistant MVP."""
from __future__ import annotations

import sys
from typing import Any, Dict, List

from .conversation import collect_requirements, summarize_requirements
from .memory import PreferenceMemory
from .ranking import score_products
from .retrieval import search_products
from .config import get_model_catalog
from .llm import moderate


def _parse_budget(value: str) -> float:
    cleaned = value.replace("CHF", "").replace("–", "").replace("'", "").strip()
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _derive_query_terms(requirements: Dict[str, Any]) -> List[str]:
    terms: List[str] = []
    for key in ("primary_use", "preference_focus"):
        value = requirements.get(key, "")
        if value:
            terms.extend([part.strip() for part in value.split(",") if part.strip()])
    return terms


def _moderate_or_exit(text: str) -> None:
    try:
        moderation = moderate(text)
    except Exception:
        return
    for result in moderation.get("results", []):
        if result.get("flagged"):
            print("⚠️ Input failed moderation. Please adjust your request.")
            sys.exit(1)


def run_cli() -> None:
    print("Buy-with-Me MVP (Swiss market)")
    catalog = get_model_catalog()
    print(f"Using primary model: {catalog.primary} | fast model: {catalog.fast}")

    category = ""
    while not category:
        category = input("Which product category are you shopping for?\n> ").strip().lower()
        if not category:
            print("Please provide a category (e.g., laptop, stroller, headphones).")
    _moderate_or_exit(category)

    memory = PreferenceMemory()
    memory.load()

    requirements = collect_requirements(memory.get_latest())
    for answer in requirements.values():
        _moderate_or_exit(answer)

    summary = summarize_requirements({**requirements, "category": category})
    print("\nSummary of your needs:")
    print(summary)
    confirm = input("Does this look correct? (y/n)\n> ").strip().lower()
    if confirm not in {"y", "yes"}:
        print("Let's capture your answers again.")
        requirements = collect_requirements(memory.get_latest())
        summary = summarize_requirements({**requirements, "category": category})
        print("\nUpdated summary:")
        print(summary)

    budget_value = _parse_budget(requirements.get("budget_chf", ""))
    requirements_payload = {
        "summary": summary,
        "budget_chf": budget_value,
        "raw_answers": requirements,
        "category": category,
        "locale": "CH",
    }

    query_terms = _derive_query_terms(requirements)
    products = search_products(category, query_terms)
    if not products and query_terms:
        products = search_products(category, [])
    if not products:
        print("No products found from Digitec/Galaxus for that query. Try adjusting your constraints.")
        sys.exit(0)

    products_payload = [product.to_dict() for product in products]
    rankings = score_products(requirements_payload, products_payload)
    if not rankings:
        print("Ranking service returned no results. Please try again later.")
        sys.exit(0)

    print("\nTop recommendations (tailored to Switzerland):")
    for item in rankings[:3]:
        price = item.get("price_chf") or next(
            (p["price_chf"] for p in products_payload if p["product_id"] == item.get("product_id")),
            None,
        )
        price_str = f"CHF {price:.2f}" if isinstance(price, (int, float)) else str(price)
        print("-" * 60)
        print(f"Rank {item.get('rank')}: {item.get('product_id')}")
        print(f"Price: {price_str}")
        print(f"Specs: {item.get('key_specs')}")
        print(f"Rationale: {item.get('rationale')}")
        print(f"Link: {item.get('link')}")

    print("-" * 60)
    remember = input("Save budget and preference focus for future sessions? (y/n)\n> ").strip().lower()
    if remember in {"y", "yes"}:
        memory.update(
            {
                "budget_chf": budget_value,
                "preference_focus": requirements.get("preference_focus"),
                "primary_use": requirements.get("primary_use"),
            }
        )
        print("Preferences saved.")
    print("Thank you for using Buy-with-Me!")


if __name__ == "__main__":
    run_cli()
