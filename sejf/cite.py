"""Tryb cytatu: model WYBIERA dosłowne jednostki tekstu źródeł (§, ustęp, punkt, zdanie) + jedno zdanie wniosku.

Cytaty są poprawne z konstrukcji (to fragmenty źródła, weryfikowalne porównaniem napisów).
Jedyny tekst generowany - "wniosek" - przechodzi przez weryfikator jak w trybie odpowiedzi.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .core import REFUSAL_TEXT, Source

CITE_SYSTEM = (
    "Pomagasz znaleźć w przepisach fragmenty, które odpowiadają na pytanie. Masz ponumerowane fragmenty [S1], [S2]...\n"
    "1. Wybierz WYŁĄCZNIE numery fragmentów, które bezpośrednio odpowiadają na pytanie (zwykle 1-3).\n"
    "2. Napisz jedno krótkie zdanie wniosku wynikające tylko z wybranych fragmentów (z liczbami i warunkami).\n"
    "3. Jeśli żaden fragment nie odpowiada na pytanie, zwróć pustą listę i pusty wniosek.\n"
    'Odpowiedz wyłącznie JSON-em: {"fragmenty": ["S3", "S7"], "wniosek": "..."}'
)

_UNIT_SPLIT = re.compile(r"(?m)(?=^\s*(?:Art\.\s*\d+[a-z¹²³⁴⁵⁶⁷⁸⁹⁰]*\.|§\s*\d+[a-z¹²³⁴⁵⁶⁷⁸⁹⁰]*\.|\d+[a-z]?\.\s|\d+[a-z]?\)\s))")


@dataclass
class Unit:
    sid: str
    source_n: int
    text: str


@dataclass
class CiteAnswer:
    status: str                 # answered | refused
    quotes: list = field(default_factory=list)   # [Unit]
    conclusion: str = ""
    conclusion_support: float | None = None
    conclusion_ok: bool | None = None
    raw: str = ""


def units(sources: list[Source], max_units: int = 60, max_chars: int = 600) -> list[Unit]:
    """Dzieli źródła na jednostki redakcyjne; zbyt długie tnie po zdaniach."""
    out = []
    for s in sources:
        for chunk in _UNIT_SPLIT.split(s.text):
            chunk = re.sub(r"\s+", " ", chunk).strip()
            if len(chunk) < 15:
                continue
            pieces = [chunk] if len(chunk) <= max_chars else re.split(r"(?<=[.;])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])", chunk)
            buf = ""
            for p in pieces:
                if buf and len(buf) + len(p) > max_chars:
                    out.append(Unit(f"S{len(out)+1}", s.n, buf.strip())); buf = ""
                buf += " " + p
            if buf.strip():
                out.append(Unit(f"S{len(out)+1}", s.n, buf.strip()))
            if len(out) >= max_units:
                return out
    return out


def build_messages(question: str, us: list[Unit]):
    body = "\n".join(f"[{u.sid}] {u.text}" for u in us)
    return [{"role": "system", "content": CITE_SYSTEM},
            {"role": "user", "content": f"Fragmenty:\n{body}\n\nPytanie: {question}"}]


def parse(raw: str, us: list[Unit]):
    by = {u.sid: u for u in us}
    m = re.search(r"\{.*\}", raw or "", re.S)
    sel, concl = [], ""
    if m:
        try:
            d = json.loads(m.group(0))
            sel = [str(x).strip().upper().strip("[]") for x in (d.get("fragmenty") or [])]
            concl = str(d.get("wniosek") or "").strip()
        except Exception:
            pass
    if not sel:  # model nie dał JSON - wyciągamy S\d+ z tekstu
        sel = re.findall(r"\bS(\d{1,3})\b", raw or "")
        sel = [f"S{x}" for x in sel]
    quotes, seen = [], set()
    for sid in sel:
        if sid in by and sid not in seen:
            quotes.append(by[sid]); seen.add(sid)
    return quotes[:4], concl


def ask(question, retriever, generator, verifier=None, threshold=0.5, k=5):
    sources = retriever(question, k)
    for i, s in enumerate(sources, 1):
        s.n = i
    us = units(sources)
    if not us:
        return CiteAnswer("refused", conclusion=REFUSAL_TEXT), sources, us
    raw = generator(build_messages(question, us))
    quotes, concl = parse(raw, us)
    if not quotes:
        return CiteAnswer("refused", conclusion=REFUSAL_TEXT, raw=raw), sources, us
    a = CiteAnswer("answered", quotes=quotes, conclusion=concl, raw=raw)
    if concl and verifier is not None:
        ctx = " ".join(q.text for q in quotes)
        a.conclusion_support = float(verifier([(concl, ctx)])[0])
        a.conclusion_ok = a.conclusion_support >= threshold
    return a, sources, us
