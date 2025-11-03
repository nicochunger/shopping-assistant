"""Application configuration constants."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelCatalog:
    primary: str = os.getenv("PRIMARY_MODEL", "gpt-5")
    fast: str = os.getenv("FAST_MODEL", "gpt-5-mini")
    embeddings: str = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-large")
    moderation: str = os.getenv("MODERATION_MODEL", "omni-moderation-latest")
    transcription: str = os.getenv("TRANSCRIPTION_MODEL", "whisper-1")


def get_model_catalog() -> ModelCatalog:
    """Return configured model catalog."""
    return ModelCatalog()


DATA_DIR = os.getenv("SHOPPING_ASSISTANT_DATA", "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")
PRODUCT_CACHE_DIR = os.path.join(DATA_DIR, "product_cache")

DEFAULT_SEARCH_RETAILERS = ["digitec", "galaxus"]
DEFAULT_MAX_PRODUCTS = int(os.getenv("MAX_PRODUCTS", "20"))
