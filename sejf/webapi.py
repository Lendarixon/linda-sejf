"""Wspólne funkcje HTTP dla aplikacji lokalnej i demo: lista dokumentów, podgląd dokumentu, zawężenie do wybranych źródeł."""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .retriever_simple import Index, read_text

MAX_DOC_CHARS = 2_000_000
UPLOAD_EXT = {".txt", ".md", ".pdf", ".docx"}


def docs_list(index: Index):
    return {"documents": index.documents(), "chunks": len(index.meta)}


def doc_text(index: Index, path: str):
    """GET /api/doc?id=<ścieżka względna> — tylko pliki obecne w indeksie (bez dostępu do innych ścieżek)."""
    q = parse_qs(urlparse(path).query)
    doc_id = (q.get("id") or [""])[0]
    p = index.file_by_id(doc_id)
    if p is None:
        return None
    return {"id": doc_id, "name": p.stem, "text": read_text(p)[:MAX_DOC_CHARS]}


def set_scope(index: Index, ids):
    """Zawęża wyszukiwanie do wybranych dokumentów (None / pusta lista = wszystkie)."""
    if not ids:
        index.only_files = None
        return
    files = {str(p) for p in (index.file_by_id(str(i)) for i in ids) if p is not None}
    index.only_files = files or None


_BAD = set('<>:"/\\|?*') | {chr(i) for i in range(32)}
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_upload_name(name: str):
    """Tylko nazwa pliku (bez katalogów), dozwolone rozszerzenia, nazwa poprawna w Windows; None gdy nie wolno."""
    base = Path(str(name).replace("\\", "/")).name.strip().rstrip(". ")
    if not base or base.startswith(".") or Path(base).suffix.lower() not in UPLOAD_EXT:
        return None
    if any(c in _BAD for c in base) or Path(base).stem.upper() in _RESERVED or len(base) > 180:
        return None
    return base


# ---------------------------------------------------------------- wyszukiwanie fragmentów (panel źródeł)
_PHRASE = re.compile(r'["„“”]([^"„“”]{2,})["„“”]')
_TOKEN = re.compile(r"\S+")


def parse_query(q: str):
    """Składnia wyszukiwania: „dokładna fraza” w cudzysłowie, -słowo (wyklucz), kody i liczby (art. 22, BR105) muszą
    wystąpić. Zwraca (tekst do wyszukiwania znaczeniowego, frazy, wykluczone słowa, kody)."""
    q = str(q or "")[:300]
    phrases = [m.strip().lower() for m in _PHRASE.findall(q)]
    rest = _PHRASE.sub(" ", q)
    excludes, codes, words = [], [], []
    for t in _TOKEN.findall(rest):
        if t.startswith("-") and len(t) > 2:
            excludes.append(t[1:].lower())
        else:
            words.append(t)
            core = t.strip(".,;:()[]").lower()
            if any(ch.isdigit() for ch in core) and len(core) >= 2:
                codes.append(core)
    text = " ".join(words + phrases).strip()
    return text, phrases, excludes, codes


def _rel_id(index: Index, f: str) -> str:
    try:
        return str(Path(f).relative_to(index.folder)).replace("\\", "/")
    except ValueError:
        return Path(f).name


def _has(text: str, phrases, codes, excludes) -> bool:
    t = text.lower()
    if any(ph not in t for ph in phrases):
        return False
    if any(not re.search(r"(?<![\w])" + re.escape(c) + r"(?![\w])", t) for c in codes):
        return False
    return not any(re.search(r"(?<![\w])" + re.escape(x), t) for x in excludes)


def _snippet(text: str, terms, width: int = 320) -> str:
    t = text.lower()
    # najdłuższy (najbardziej konkretny) termin, który występuje: fraza albo kod przed pojedynczym słowem
    pos = next((i for i in (t.find(x) for x in terms if x) if i >= 0), 0)
    a = max(0, pos - width // 3)
    return ("…" if a else "") + text[a:a + width].strip() + ("…" if a + width < len(text) else "")


def search_fragments(index: Index, q: str, k: int = 12):
    """Wyszukiwanie fragmentów dla człowieka: ten sam hybrydowy wyszukiwacz co dla modelu (e5 + BM25 + reranker),
    plus dokładne frazy, kody i wykluczenia. Zakres jak przy pytaniach (index.only_files)."""
    text, phrases, excludes, codes = parse_query(q)
    if not text and not phrases:
        return {"query": q, "hits": [], "terms": []}
    hits = index.search(text, k * 2) if text else []
    order = {}
    for h in hits:
        order.setdefault((h["file"], h["start_line"]), len(order))
    exact = []
    if phrases or codes:
        allowed = index.only_files
        for m in index.meta:
            if allowed and m["file"] not in allowed:
                continue
            if _has(m["text"], phrases, codes, excludes):
                exact.append(m)
                if len(exact) >= 400:
                    break
        exact.sort(key=lambda m: (order.get((m["file"], m["start_line"]), 10 ** 6), m["file"], m["start_line"]))
        rows = [{"file": m["file"], "start_line": m["start_line"], "end_line": m.get("end_line"), "text": m["text"],
                 "score": None} for m in exact[:k]]
    else:
        rows = [{"file": h["file"], "start_line": h["start_line"], "end_line": None, "text": h["snippet"],
                 "score": h.get("rerank_score")} for h in hits if _has(h["snippet"], [], [], excludes)][:k]
    terms = sorted({*phrases, *codes, *[w.lower() for w in re.findall(r"\w{4,}", text)]}, key=len, reverse=True)
    out = [{"id": _rel_id(index, r["file"]), "name": Path(r["file"]).stem, "line": r["start_line"],
            "snippet": _snippet(r["text"], terms), "text": r["text"], "score": r["score"]} for r in rows]
    return {"query": q, "hits": out, "terms": terms[:12], "exact": bool(phrases or codes)}
