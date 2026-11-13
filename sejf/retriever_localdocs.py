"""Adapter: wyszukiwarka LocalDocs (project_search) -> źródła Sejfu.

Uprawnienia: przekazujemy allowed_folders z serwera LocalDocs (token + grupy),
więc fragmenty z folderów, do których użytkownik nie ma dostępu, nigdy nie
trafiają do modelu językowego.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from .core import Source
from .labels import legal_label, superscripts  # noqa: F401

def _free_any(folders, query, k):
    """Wersja bez wyszukiwania semantycznego (LocalDocs Free): wyszukiwanie dokładnych słów wymaga WSZYSTKICH słów
    pytania w jednym fragmencie, więc dla pytania zwykle zwraca 0. Tu: BM25 po dowolnym słowie (OR), łączone z folderów."""
    try:
        import probe_text_index as _pti
    except ImportError:
        return []
    hits = []
    for f in folders:
        try:
            hits += _pti.search(f, query, k, match="any")
        except Exception:
            continue
    hits.sort(key=lambda h: -float(h.get("score", 0.0)))
    return hits[:k]


def make_retriever(backend, folders=None, per_shard=None):
    """backend = moduł project_search.backend. folders=None -> wszystkie indeksy dozwolone przez serwer."""
    def retrieve(query: str, k: int):
        if folders and len(folders) == 1:
            hits = backend.search_project(folders[0], query, k)
        else:
            hits = backend.search_all(query, k=k, per_shard=per_shard or k, allowed_folders=folders)
        if not hits and folders:
            # bez wyszukiwania semantycznego: reranker też tutaj, inaczej bramka odmowy (min_rerank_score) nie działa
            try:
                from project_search import rerank as _rr
            except ImportError:
                _rr = None
            if _rr is not None and _rr.enabled():
                hits = _rr.rerank(query, _free_any(folders, query, max(k, 30)), max(k, 30))
            else:
                hits = _free_any(folders, query, k)
        out = []
        for h in hits[:k]:
            out.append(Source(
                n=0,
                text=superscripts(h.get("snippet", "")),
                file=h.get("file", ""),
                locator=h.get("locator", ""),
                label=legal_label(h.get("file", ""), h.get("start_line"), h.get("snippet", "")),
                score=float(h.get("score", 0.0)),
                rerank=float(h["rerank_score"]) if h.get("rerank_score") is not None else None,
            ))
        return out
    return retrieve
