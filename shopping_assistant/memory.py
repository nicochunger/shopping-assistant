"""Simple preference memory management."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict

from .config import MEMORY_FILE, DATA_DIR

ISO_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"
EXPIRY_DAYS = 90


@dataclass
class PreferenceMemory:
    data: Dict[str, Any] = field(default_factory=dict)

    def load(self) -> None:
        if not os.path.exists(MEMORY_FILE):
            self.data = {}
            return
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as handle:
                self.data = json.load(handle)
        except (json.JSONDecodeError, OSError):
            self.data = {}

    def save(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MEMORY_FILE, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, ensure_ascii=False, indent=2)

    def get_latest(self) -> Dict[str, Any]:
        self.prune_expired()
        return self.data.get("preferences", {})

    def update(self, new_prefs: Dict[str, Any]) -> None:
        self.data.setdefault("preferences", {})
        self.data["preferences"].update(new_prefs)
        self.data["updated_at"] = datetime.utcnow().strftime(ISO_FMT)
        self.save()

    def prune_expired(self) -> None:
        timestamp = self.data.get("updated_at")
        if not timestamp:
            return
        try:
            updated = datetime.strptime(timestamp, ISO_FMT)
        except ValueError:
            self.data = {}
            self.save()
            return
        if datetime.utcnow() - updated > timedelta(days=EXPIRY_DAYS):
            self.data = {}
            self.save()
