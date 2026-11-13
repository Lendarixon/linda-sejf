"""Etykiety źródeł dla tekstów ustaw: 'Kodeks pracy, art. 22²'."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_ART = re.compile(r"(?m)^\s*Art\.\s*(\d+[a-z]*(?:\[\d+\])?)\.")
_SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def superscripts(text: str) -> str:
    """'Art. 22[1].' -> 'Art. 22¹.' (indeks górny z PDF Dziennika Ustaw; bez kolizji z odwołaniami [n])."""
    return re.sub(r"(\d[a-z]?)\[(\d{1,2})\]", lambda m: m.group(1) + m.group(2).translate(_SUP), text)
_TITLE = re.compile(r"(?:o|w sprawie)\s+ogłoszenia\s+jednolitego\s+tekstu\s+(.+?)\s*\n", re.S)


@lru_cache(maxsize=256)
def _file_lines(path: str):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


@lru_cache(maxsize=256)
def _doc_title(path: str):
    lines = _file_lines(path)
    head = "\n".join(lines[:40])
    m = _TITLE.search(head)
    if m:
        t = re.sub(r"\s+", " ", m.group(1)).strip()
        t = re.sub(r"^ustawy\s*[–-]\s*", "", t)
        return re.sub(r"^ustawy ", "ustawa ", t)
    return Path(path).stem


def _is_body_line(line: str) -> bool:
    """Nagłówki ('Urlopy wypoczynkowe', 'Rozdział IV', 'DZIAŁ SIÓDMY') nie mają numeracji
    jednostek ani kropki na końcu; treść przepisu - tak."""
    t = line.strip()
    if re.match(r"^(§\s*\d|\d+[a-z]*[.)]|[a-z]\))", t) or t.endswith((".", ";", ",", ":", "-", "–")):
        return True
    # zawinięte wiersze treści są długie albo zaczynają się małą literą; nagłówki - krótkie, wielką literą
    return len(t) > 60 or t[:1].islower()


def chunk_articles(file: str, start_line: int | None, snippet: str) -> list:
    """Artykuły obecne we fragmencie, w kolejności. Jeśli fragment zaczyna się w środku
    artykułu (przed pierwszym 'Art.' jest treść, a nie sam nagłówek rozdziału), dołączamy
    artykuł poprzedzający z pliku."""
    found = [m.group(1) for m in _ART.finditer(snippet)]
    first = _ART.search(snippet)
    prefix = snippet[: first.start()] if first else snippet
    prefix_is_body = any(_is_body_line(l) for l in prefix.splitlines() if l.strip())
    arts = []
    if (prefix_is_body or not first) and start_line:
        lines = _file_lines(file)
        for i in range(min(start_line, len(lines)) - 2, max(-1, start_line - 400), -1):
            mm = _ART.match(lines[i])
            if mm:
                arts.append(mm.group(1))
                break
    for a in found:
        if a not in arts:
            arts.append(a)
    return arts


def legal_label(file: str, start_line: int | None, snippet: str) -> str:
    """'Kodeks pracy, art. 151, 152' - artykuły, których treść jest we fragmencie."""
    title = _doc_title(file)
    arts = chunk_articles(file, start_line, snippet)
    return f"{title}, art. {', '.join(superscripts(a) for a in arts)}" if arts else title
