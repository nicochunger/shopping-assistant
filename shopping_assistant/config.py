"""
Configuration loading for the shopping assistant via environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.
    """

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    clarification_model: str = Field(
        default="gpt-5-mini", alias="OPENAI_CLARIFICATION_MODEL"
    )
    research_model: str = Field(
        default="gpt-5", alias="OPENAI_RESEARCH_MODEL"
    )
    tavily_api_key: Optional[str] = Field(default=None, alias="TAVILY_API_KEY")
    tavily_search_depth: str = Field(default="advanced", alias="TAVILY_SEARCH_DEPTH")
    clarification_question_limit: int = Field(
        default=6, alias="ASSISTANT_MAX_QUESTIONS"
    )
    recommendation_count: int = Field(
        default=3, alias="ASSISTANT_RECOMMENDATION_COUNT"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Load settings once for the lifetime of the process.
    """

    try:
        return Settings()
    except ValidationError as exc:  # pragma: no cover - configuration errors surface early
        missing = {err["loc"][0] for err in exc.errors() if err["type"] == "missing"}
        message = (
            "Missing required configuration: "
            + ", ".join(sorted(name.upper() for name in missing))
        )
        raise RuntimeError(message) from exc
