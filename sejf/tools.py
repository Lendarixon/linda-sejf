"""Narzędzia jak w NotebookLM, ale lokalnie: streszczenie, terminy/kwoty/obowiązki, notatka służbowa.

Każde zdanie albo wiersz wyniku ma odwołanie [n] do fragmentu i przechodzi przez ten sam weryfikator zdań co odpowiedzi.
Krótkie dokumenty idą do modelu w całości; z długich (np. ustaw) wybieramy fragmenty pasujące do podanego tematu.
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

from .core import REFUSAL_TEXT, Answer, Source, is_refusal, split_sentences
from .labels import legal_label, superscripts

import re

_INTRO = re.compile(r"^\W*(poniżej|oto|przedstawiam|notatka|podsumowanie|streszczenie)\b", re.I)
MAX_FULL_CHUNKS = 24      # ok. 15 tys. znaków — mieści się w kontekście modelu razem z odpowiedzią
TOPIC_K = 8

SYSTEM = ("Jesteś asystentem biurowym. Pracujesz wyłącznie na podanych fragmentach dokumentów, po polsku. "
          "Każde zdanie albo wiersz kończysz odwołaniem w nawiasie kwadratowym do numeru fragmentu, np. [2]. "
          "Nie dodajesz wiedzy spoza fragmentów, nie zgadujesz i nie dajesz własnych rad. Zachowujesz warunki i wyjątki (np. „w jedną stronę”, „chyba że…”, kogo i czego dotyczy zasada). Gdy fragmenty nie zawierają potrzebnych informacji, "
          "odpowiadasz dokładnie: BRAK_ODPOWIEDZI.")

TOOLS = {
    "summary": {
        "name": "Streszczenie",
        "prompt": ("Streść poniższe dokumenty w 5–8 zdaniach. Pierwsze zdanie: czego dotyczy dokument. Potem najważniejsze "
                   "zasady, terminy i kwoty. Każde zdanie zakończ odwołaniem [n]."),
    },
    "facts": {
        "name": "Terminy, kwoty i obowiązki",
        "prompt": ("Wypisz z fragmentów terminy, kwoty, limity i obowiązki — najwyżej 20 pozycji, najważniejsze najpierw. "
                   "Każda pozycja w osobnym wierszu, w formacie: „- co: termin, kwota albo limit (kogo dotyczy) [n]”. "
                   "Przepisuj liczby dokładnie tak, jak są we fragmentach."),
    },
    "memo": {
        "name": "Notatka służbowa",
        "prompt": ("Napisz krótką notatkę służbową na temat: {topic}. Bez tytułu i bez zdań typu „poniżej przedstawiam”. "
                   "Najpierw jedno zdanie: czego dotyczą zasady, potem 3–6 punktów z najważniejszymi ustaleniami — tylko to, co jest zapisane we fragmentach, "
                   "bez własnych wniosków i zaleceń. Każde zdanie i każdy punkt zakończ odwołaniem [n]. "
                   "Jeśli fragmenty nie dotyczą tego tematu, odpowiedz BRAK_ODPOWIEDZI."),
    },
}


def gather_sources(index, doc_ids, topic: str = ""):
    """Fragmenty do narzędzia: całe krótkie dokumenty albo fragmenty pasujące do tematu. Zwraca (źródła, opis)."""
    files = [p for p in (index.file_by_id(str(i)) for i in (doc_ids or [])) if p is not None]
    if not files:
        files = sorted({Path(m["file"]) for m in index.meta})
    wanted = {str(f) for f in files}
    chunks = [m for m in index.meta if m["file"] in wanted]
    if chunks and len(chunks) <= MAX_FULL_CHUNKS:
        order = {str(f): k for k, f in enumerate(files)}
        chunks.sort(key=lambda m: (order.get(m["file"], 0), m["start_line"]))
        src = [Source(n=i, text=superscripts(m["text"]), file=m["file"], locator=f"lines {m['start_line']}-{m['end_line']}",
                      label=legal_label(m["file"], m["start_line"], m["text"])) for i, m in enumerate(chunks, 1)]
        return src, "cały dokument" if len(files) == 1 else f"całe dokumenty ({len(files)})"
    if not topic.strip():
        raise ValueError("Wybrane dokumenty są za długie, żeby przetworzyć je w całości. Zaznacz po lewej jeden "
                         "dokument (np. „Regulamin pracy”) albo użyj notatki służbowej z tematem "
                         "(np. „urlop wypoczynkowy”) — wtedy Sejf weźmie pasujące fragmenty.")
    prev = index.only_files
    index.only_files = wanted
    try:
        hits = index.search(topic, TOPIC_K)
    finally:
        index.only_files = prev
    src = [Source(n=i, text=superscripts(h["snippet"]), file=h["file"], locator=h["locator"],
                  label=legal_label(h["file"], h["start_line"], h["snippet"]), rerank=h.get("rerank_score"))
           for i, h in enumerate(hits, 1)]
    return src, f"fragmenty pasujące do tematu „{topic.strip()}”"


def build_messages(tool: str, sources, topic: str = ""):
    blocks = [f"[{s.n}] {s.label}\n{s.text}" for s in sources]
    task = TOOLS[tool]["prompt"].format(topic=topic.strip() or "najważniejsze informacje z dokumentów")
    user = "Fragmenty dokumentów:\n\n" + "\n\n".join(blocks) + f"\n\nZadanie: {task}"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def run_tool(sejf, index, generate_long, tool: str, doc_ids=None, topic: str = "", user: str = "local") -> dict:
    if tool not in TOOLS:
        raise ValueError("Nieznane narzędzie.")
    if tool == "memo" and not topic.strip():
        raise ValueError("Wpisz temat notatki.")
    t0 = time.perf_counter()
    sources, scope = gather_sources(index, doc_ids, topic)
    for s in sources:
        s.sha256 = hashlib.sha256(s.text.encode("utf-8")).hexdigest()
    title = TOOLS[tool]["name"] + (f": {topic.strip()}" if topic.strip() else "")
    if not sources:
        ans = Answer(title, "no_sources", REFUSAL_TEXT, timings={"retrieval_s": time.perf_counter() - t0})
        sejf._audit(ans, user)
        return {**ans.to_dict(), "tool": tool, "scope": scope}
    t1 = time.perf_counter()
    raw = generate_long(build_messages(tool, sources, topic))
    t2 = time.perf_counter()
    if is_refusal(raw):
        ans = Answer(title, "refused", REFUSAL_TEXT, sources=sources, raw=raw,
                     timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1})
    else:
        # tytuły i zdania-wstępy bez odwołania nie są twierdzeniami z dokumentu — pomijamy je
        sents = [s for s in split_sentences(raw)
                 if s.cited or (len(s.text) > 90 and not _INTRO.match(s.text))]
        sejf._verify(sents, sources)
        t3 = time.perf_counter()
        ans = Answer(title, "answered", " ".join(s.text for s in sents), sentences=sents, sources=sources, raw=raw,
                     timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1, "verify_s": t3 - t2})
    sejf._audit(ans, user)
    return {**ans.to_dict(), "tool": tool, "scope": scope}
