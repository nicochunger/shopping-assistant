"""Tests for the research agent pipeline."""

from __future__ import annotations

from types import SimpleNamespace

from shopping_assistant.research import ResearchAgent, SearchResult


class FakeLLM:
    """Minimal stub returning queued JSON payloads."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests: list[dict] = []

    def generate_json(self, system_prompt, messages):
        self.requests.append({"system": system_prompt, "messages": messages})
        try:
            return self._responses.pop(0)
        except IndexError as exc:  # pragma: no cover - defensive guardrail
            raise AssertionError("LLM called more times than expected") from exc


class FakeSearchClient:
    """Records batch search requests for verification."""

    def __init__(self, payload=None):
        self.payload = payload or {}
        self.batch_calls: list[dict] = []

    def batch_search(self, queries, max_results):
        self.batch_calls.append({"queries": list(queries), "max_results": max_results})
        if self.payload:
            return self.payload
        return {query: [] for query in queries}


def build_settings():
    return SimpleNamespace(
        tavily_search_depth="advanced",
        recommendation_count=2,
    )


def test_collect_research_uses_injected_search_client():
    fake_llm = FakeLLM([])
    fake_search = FakeSearchClient()
    agent = ResearchAgent(fake_llm, build_settings(), search_client=fake_search)

    result = agent.collect_research(["espresso"], per_query_results=3)

    assert result == {"espresso": []}
    assert fake_search.batch_calls == [{"queries": ["espresso"], "max_results": 3}]


def test_recommend_products_filters_unknown_urls():
    fake_llm = FakeLLM(
        [
            {
                "recommendations": [
                    {
                        "name": "Ground Control 155",
                        "url": "https://shop.example.com/ground-control?ref=ads",
                        "why_it_fits": "Swiss retailer with grinder presets.",
                        "highlights": ["Low retention", "Quiet"],
                        "watchouts": ["Large countertop footprint"],
                        "best_for": "Home espresso obsessives",
                    },
                    {
                        "name": "Imaginary Machine",
                        "url": "https://totallyfake.invalid/product",
                        "why_it_fits": "",
                        "highlights": [],
                        "watchouts": [],
                        "best_for": "",
                    },
                ],
                "comparison_insight": "The Ground Control balances value with Swiss support.",
            }
        ]
    )
    agent = ResearchAgent(fake_llm, build_settings(), search_client=FakeSearchClient())
    research_payload = {
        "espresso": [
            SearchResult(
                title="Ground Control 155",
                url="https://shop.example.com/ground-control",
                snippet="Product page",
            )
        ]
    }

    result = agent.recommend_products("espresso machine", "", research_payload)

    assert len(result["recommendations"]) == 1
    assert result["recommendations"][0].name == "Ground Control 155"
    assert result["discarded_count"] == 1
