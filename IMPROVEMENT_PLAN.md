# Improvement Implementation Plan

## 1. Enforce Structured JSON Handling in `LLMClient`
1. Leverage the OpenAI SDK's structured response interface (e.g., `responses.parse` or `response_format`) so completions are forced to return JSON.
2. Update `LLMClient.generate`/`generate_json` to request the stricter format and keep a defensive fallback that retries or raises a clearer error when parsing fails.
3. Add unit coverage for `_strip_code_fence` fallback behaviour (if reasonable) or at least ensure new code paths are exercised via mocks.

## 2. Guard Against Hallucinated Recommendation URLs
1. Extend `ResearchAgent.recommend_products` to collect the set of URLs present in Tavily search results (normalized).
2. When iterating over LLM output, only accept recommendations whose `url` matches a known search URL; drop or flag mismatches.
3. Surface a warning when options were discarded so the CLI can inform the user, and consider including the count of filtered items in the comparison insight or via console messaging.

## 3. Fail Fast on Missing Tavily Configuration
1. Validate Tavily prerequisites before commencing clarification by trying to initialize `ResearchAgent` (or a lighter check) immediately after loading settings.
2. If Tavily configuration is missing, raise the same RuntimeError so the CLI can exit before asking questions.
3. Adjust CLI flow/tests to reflect the new order of operations.

## 4. Make Research Pipeline Testable Offline
1. Allow `ResearchAgent` to accept an optional `SearchClient` (or protocol) so tests can inject a fake backend instead of calling Tavily.
2. Add pytest coverage that fakes search results to exercise `_format_research`, query crafting, and recommendation parsing logic using stubbed LLM/Search clients.
3. Ensure new tests live under `tests/test_research.py` mirroring the package structure.

## 5. Improve Error Reporting Granularity
1. Break the large `try` block in `cli.py` into smaller sections around query generation, search collection, and recommendation synthesis.
2. When an exception occurs, include the stage name and exception details in the message while still exiting gracefully.
3. Consider logging debug context (e.g., last crafted queries) or printing next steps for the user while keeping secrets out of output.
