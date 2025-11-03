"""Product retrieval from Digitec/Galaxus."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

import requests

from .config import PRODUCT_CACHE_DIR, DEFAULT_MAX_PRODUCTS

DIGITEC_MARKDOWN_ENDPOINT = "https://r.jina.ai/https://www.digitec.ch/en/s1/search"


@dataclass
class Product:
    product_id: str
    name: str
    brand: str
    price_chf: float
    price_raw: str
    specs_summary: str
    link: str
    retailer: str = "digitec"

    def to_dict(self) -> dict:
        return asdict(self)


def _cache_path(query: str) -> Path:
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()
    return Path(PRODUCT_CACHE_DIR) / f"digitec_{digest}.json"


def _parse_price(raw: str) -> float:
    normalized = raw.replace("CHF", "").replace(".–", "").replace("–", "").replace("'", "").strip()
    normalized = normalized.replace(" ", "")
    normalized = normalized.replace(",", ".")
    try:
        return float(normalized)
    except ValueError:
        return 0.0


def _parse_brand_and_name(raw: str) -> tuple[str, str]:
    brand_match = re.match(r"\*\*(.*?)\*\*(.*)", raw)
    if not brand_match:
        return "", raw.strip()
    brand = brand_match.group(1).strip()
    name = brand_match.group(2).strip()
    return brand, name


def _parse_markdown(markdown: str, limit: int) -> List[Product]:
    """Parse Digitec markdown search results into products."""

    chunks = markdown.split("[](")
    products: List[Product] = []
    for chunk in chunks[1:]:
        if len(products) >= limit:
            break
        try:
            link_part, remainder = chunk.split(")", 1)
        except ValueError:
            continue
        link = link_part.strip()
        if not link.startswith("https://www.digitec.ch"):
            continue
        lines = [line.strip() for line in remainder.splitlines() if line.strip()]
        price_raw = ""
        brand = ""
        name = ""
        specs = ""
        for line in lines:
            if not price_raw and line.startswith("CHF"):
                price_raw = line
            elif not name and line.startswith("**"):
                brand, name = _parse_brand_and_name(line)
            elif (
                not specs
                and not line.startswith("![")
                and not line.startswith("CHF")
                and not line.startswith("**")
            ):
                if "galaxus" in line.lower():
                    continue
                specs = line
        if link and name and price_raw:
            product_id = link.rstrip("/").split("-")[-1]
            products.append(
                Product(
                    product_id=product_id,
                    name=name,
                    brand=brand,
                    price_chf=_parse_price(price_raw),
                    price_raw=price_raw,
                    specs_summary=specs,
                    link=link,
                )
            )
    return products[:limit]


def fetch_digitec_products(query: str, *, limit: int = DEFAULT_MAX_PRODUCTS, force_refresh: bool = False) -> List[Product]:
    cache_file = _cache_path(query)
    if cache_file.exists() and not force_refresh:
        try:
            return [Product(**item) for item in json.loads(cache_file.read_text(encoding="utf-8"))]
        except (json.JSONDecodeError, TypeError):
            cache_file.unlink(missing_ok=True)
    params = {"q": query}
    response = requests.get(DIGITEC_MARKDOWN_ENDPOINT, params=params, timeout=30)
    response.raise_for_status()
    products = _parse_markdown(response.text, limit)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps([p.to_dict() for p in products], ensure_ascii=False, indent=2), encoding="utf-8")
    return products


def search_products(category: str, query_terms: List[str], limit: int = 12) -> List[Product]:
    query = " ".join([category, *query_terms]).strip()
    seen = set()
    results: List[Product] = []
    for product in fetch_digitec_products(query, limit=limit * 2):
        if product.product_id in seen:
            continue
        results.append(product)
        seen.add(product.product_id)
        if len(results) >= limit:
            break
    return results
