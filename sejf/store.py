"""Lokalny zapis rozmów i wyników studia: jeden plik JSON na wpis w folderze danych programu.

Nic nie wychodzi poza komputer. Kolekcje są z listy dozwolonych, a identyfikatory — krótkie i bezpieczne dla nazw plików.
"""
from __future__ import annotations

import json
import re
import secrets
import time
from pathlib import Path

COLLECTIONS = ("rozmowy", "studio")
MAX_BYTES = 4_000_000
_ID = re.compile(r"^[a-z0-9-]{6,40}$")


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _dir(self, c: str) -> Path:
        if c not in COLLECTIONS:
            raise ValueError("Nieznana kolekcja.")
        d = self.root / c
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _path(self, c: str, item_id: str) -> Path:
        if not isinstance(item_id, str) or not _ID.match(item_id):
            raise ValueError("Nieprawidłowy identyfikator.")
        return self._dir(c) / f"{item_id}.json"

    def list(self, c: str, limit: int = 300):
        out = []
        for p in self._dir(c).glob("*.json"):
            try:
                d = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            out.append({"id": d.get("id"), "title": d.get("title", ""), "updated": d.get("updated", 0),
                        "kind": d.get("kind", ""), "count": d.get("count", 0)})
        out.sort(key=lambda x: x["updated"], reverse=True)
        return out[:limit]

    def get(self, c: str, item_id: str):
        p = self._path(c, item_id)
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

    def save(self, c: str, obj: dict) -> dict:
        item_id = obj.get("id") or time.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)
        d = {"id": item_id, "title": str(obj.get("title", ""))[:200], "kind": str(obj.get("kind", ""))[:40],
             "count": int(obj.get("count", 0) or 0), "updated": time.time(), "data": obj.get("data")}
        raw = json.dumps(d, ensure_ascii=False)
        if len(raw.encode("utf-8")) > MAX_BYTES:
            raise ValueError("Wpis jest za duży do zapisania.")
        p = self._path(c, item_id)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(raw, encoding="utf-8")
        tmp.replace(p)
        return {k: d[k] for k in ("id", "title", "kind", "count", "updated")}

    def delete(self, c: str, item_id: str) -> bool:
        p = self._path(c, item_id)
        if p.exists():
            p.unlink()
            return True
        return False
