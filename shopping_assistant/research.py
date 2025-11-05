"""
Research stage that generates live product recommendations from search results.
"""

from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent
from typing import Dict, Iterable, List, Sequence

from tavily import TavilyClient

from .config import Settings
from .llm import LLMClient


@dataclass
class SearchResult:
    """
    Minimal representation of a product search hit.
    """

    title: str
    url: str
    snippet: str
    score: float | None = None


@dataclass
class ProductRecommendation:
    """
    Structured result returned to the CLI for display.
    """

    name: str
    url: str
    why_it_fits: str
    highlights: List[str]
    watchouts: List[str]
    best_for: str


class SearchClient:
    """
    Wrapper that hits the Tavily Search API for up-to-date product data.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.tavily_api_key:
            raise RuntimeError(
                "TAVILY_API_KEY is required for web search. "
                "Sign up at https://app.tavily.com/ to obtain an API key."
            )
        self._client = TavilyClient(api_key=settings.tavily_api_key)
        self._settings = settings

    def search(
        self, query: str, *, max_results: int = 5, include_images: bool = False
    ) -> List[SearchResult]:
        """
        Execute a Tavily search and normalise the response payload.
        """

        payload = self._client.search(
            query=query,
            max_results=max_results,
            include_images=include_images,
            search_depth=self._settings.tavily_search_depth,
        )
        results = []
        for item in payload.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title") or "Untitled result",
                    url=item.get("url") or "",
                    snippet=item.get("content") or item.get("snippet") or "",
                    score=item.get("score"),
                )
            )
        return results

    def batch_search(
        self, queries: Sequence[str], *, max_results: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """
        Run multiple queries, returning a mapping from query to results.
        """

        return {
            query: self.search(query, max_results=max_results)
            for query in queries
        }


class ResearchAgent:
    """
    Coordinates the research and recommendation phase using the LLM and search API.
    """

    QUERY_PROMPT = """
        You are helping a shopping assistant research products.
        The assistant already knows the shopper's needs and will now generate focused
        web search queries that find current products for sale.

        Respond with JSON: {"queries": [string, ...]}
        - Provide between 2 and 4 distinct queries.
        - Blend feature-specific and buyer-intent keywords.
        - Avoid redundant variations.
    """

    RECOMMENDATION_PROMPT = """
        You are a shopping expert turning live web research into product recommendations.
        Use the shopper profile and search snippets to pick concrete products available now.

        Requirements:
        - Recommend {count} products.
        - For each, provide "name", "url", "why_it_fits" (<=120 words),
          "highlights" (3 bullet strings), "watchouts" (1-2 bullet strings)
          and "best_for" (short persona style description).
        - Products must map to URLs present in the search results.
        - When evidence is weak, flag the uncertainty rather than inventing details.

        Respond strictly with JSON shaped as:
        {{
          "recommendations": [
             {{
               "name": "...",
               "url": "...",
               "why_it_fits": "...",
               "highlights": [ "...", ... ],
               "watchouts": [ "...", ... ],
               "best_for": "..."
             }}
          ],
          "comparison_insight": "succinct comparative insight"
        }}
    """

    def __init__(self, llm: LLMClient, settings: Settings) -> None:
        self._llm = llm
        self._settings = settings
        self._search = SearchClient(settings)

    def craft_search_queries(
        self, topic: str, shopper_summary: str
    ) -> List[str]:
        """
        Ask the LLM to produce targeted search queries.
        """

        content = dedent(
            f"""
            Product request: {topic}

            Shopper summary:
            {shopper_summary}
            """
        ).strip()
        payload = self._llm.generate_json(
            self.QUERY_PROMPT,
            [{"role": "user", "content": content}],
        )
        queries = payload.get("queries", [])
        if not queries:
            raise RuntimeError("LLM failed to produce search queries.")
        return [query.strip() for query in queries if query.strip()]

    def collect_research(
        self, queries: Sequence[str], *, per_query_results: int = 5
    ) -> Dict[str, List[SearchResult]]:
        """
        Run each search query and aggregate the results.
        """

        return self._search.batch_search(queries, max_results=per_query_results)

    def recommend_products(
        self,
        topic: str,
        shopper_summary: str,
        research: Dict[str, List[SearchResult]],
    ) -> Dict[str, List[ProductRecommendation] | str]:
        """
        Generate final product recommendations using the LLM.
        """

        research_text = self._format_research(research)
        prompt = dedent(
            f"""
            Product request: {topic}

            Shopper summary:
            {shopper_summary}

            Research findings:
            {research_text}

            Provide {self._settings.recommendation_count} top options.
            """
        ).strip()

        payload = self._llm.generate_json(
            self.RECOMMENDATION_PROMPT.format(
                count=self._settings.recommendation_count
            ),
            [{"role": "user", "content": prompt}],
        )

        recommendations = []
        for item in payload.get("recommendations", []):
            recommendations.append(
                ProductRecommendation(
                    name=item.get("name", "Unnamed product"),
                    url=item.get("url", ""),
                    why_it_fits=item.get("why_it_fits", ""),
                    highlights=item.get("highlights", []),
                    watchouts=item.get("watchouts", []),
                    best_for=item.get("best_for", ""),
                )
            )

        return {
            "recommendations": recommendations,
            "comparison_insight": payload.get("comparison_insight", ""),
        }

    @staticmethod
    def _format_research(
        research: Dict[str, List[SearchResult]]
    ) -> str:
        """
        Turn structured search results into a compact prompt-friendly string.
        """

        lines: List[str] = []
        for query, results in research.items():
            lines.append(f"Query: {query}")
            for result in results:
                snippet = result.snippet.replace("\n", " ").strip()
                snippet = snippet[:400]
                lines.append(
                    f"- {result.title} ({result.url}) :: {snippet}"
                )
            lines.append("")
        return "\n".join(lines).strip()
