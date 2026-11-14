"""Wspólne funkcje HTTP dla aplikacji lokalnej i demo: lista dokumentów, podgląd dokumentu, zawężenie do wybranych źródeł."""
from __future__ import annotations

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


def safe_upload_name(name: str):
    """Tylko nazwa pliku (bez katalogów), dozwolone rozszerzenia; None gdy nie wolno."""
    base = Path(str(name).replace("\\", "/")).name.strip()
    if not base or base.startswith(".") or Path(base).suffix.lower() not in UPLOAD_EXT:
        return None
    return base
