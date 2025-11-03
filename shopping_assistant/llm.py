"""Utility functions for interacting with the OpenAI API."""
from __future__ import annotations

import json
from typing import Iterable, List, Dict, Any, Optional

from openai import OpenAI

from .config import get_model_catalog

_client: Optional[OpenAI] = None


def _client_instance() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def _serialize_messages(messages: Iterable[Dict[str, str]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for message in messages:
        serialized.append(
            {
                "role": message["role"],
                "content": [{"type": "text", "text": message["content"]}],
            }
        )
    return serialized


def chat_completion(messages: Iterable[Dict[str, str]], *, model: Optional[str] = None, **kwargs: Any) -> str:
    catalog = get_model_catalog()
    model_name = model or catalog.primary
    response = _client_instance().responses.create(
        model=model_name,
        input=_serialize_messages(messages),
        **kwargs,
    )
    return response.output_text


def json_completion(messages: Iterable[Dict[str, str]], *, model: Optional[str] = None) -> Dict[str, Any]:
    raw = chat_completion(messages, model=model, response_format={"type": "json_object"})
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse JSON response: {raw}") from exc


def embed(texts: List[str]) -> List[List[float]]:
    catalog = get_model_catalog()
    response = _client_instance().embeddings.create(model=catalog.embeddings, input=texts)
    return [item.embedding for item in response.data]


def moderate(text: str) -> Dict[str, Any]:
    catalog = get_model_catalog()
    response = _client_instance().moderations.create(model=catalog.moderation, input=text)
    return response.model_dump()
