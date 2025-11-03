# Buy-with-Me MVP Plan (Switzerland Focus)

## Objectives
- Launch an MVP that captures core requirements, researches in-market products, and delivers a concise ranked shortlist tailored to Swiss availability.
- Complete the clarify loop and a single refinement loop inside one uninterrupted session.
- Track completion rate, time-to-first recommendation, and explicit user feedback as success signals.

## System Architecture
- Orchestrate reasoning and generation with `gpt-5`, reserving `gpt-5-mini` for lightweight classification, slot filling, and ranking prompts.
- Generate product embeddings using `text-embedding-3-large` and persist vectors in a lightweight store.
- Apply `omni-moderation-latest` to all inputs and outputs; add `whisper-1` only if voice capture is introduced.

## Conversation Flow
- Start by confirming product category and session mode, then collect requirements through four targeted prompts covering budget, primary use, constraints, and preference weights.
- Summarize interpreted needs with `gpt-5`, explicitly prompting the model to prioritize Swiss-market availability, and present a confirm-or-edit message before research.
- Support a single refinement turn that adjusts stored weights or constraints and reuses cached research where possible.

## Data & Retrieval
- Maintain a nightly-refreshed product catalog per category sourced from primary Swiss retailers, normalized into a shared schema with price, availability, specs, warranty, and purchase URL.
- Embed descriptions with `text-embedding-3-large`, storing citation metadata for downstream attribution.
- Escalate catalog gaps by generating structured research tasks via `gpt-5-mini` for manual follow-up.

## Ranking & Explanation
- Enforce hard constraints before scoring; then use `gpt-5-mini` to produce weighted scorecards combining normalized specs, preference weights, and availability notes.
- Convert scorecards into user-facing rationales with `gpt-5`, ensuring the prompt reinforces Swiss-tailored outputs and includes price, key specs, and purchase link for each item.
- Persist the reasoning trace for auditability.

## Memory & Preferences
- Store stable attributes (budget tier, favored brands, excluded features) with timestamps and auto-expire after 90 days without activity.
- Summarize updates using `gpt-5-mini` and surface stored preferences at session start to avoid redundant questions.

## Operations & Compliance
- Log prompts, retrieved items, ranking outputs, and feedback with personal data removed; retain source citations alongside each recommendation.
- Add scripted smoke tests that replay canonical conversations to verify Swiss-tailored prompts and ranking behavior.
- Monitor catalog freshness, API latency, and moderation outcomes, and implement escalation paths for data export or deletion requests to satisfy local regulations.
