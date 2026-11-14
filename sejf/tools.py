"""Studio jak w NotebookLM, ale lokalnie: streszczenie (długość i forma do wyboru), terminy/kwoty/obowiązki,
notatka na temat, pytania sprawdzające (fiszki), słowniczek pojęć, wyjaśnienie prostym językiem.

Każde zdanie albo wiersz wyniku ma odwołanie [n] do fragmentu i przechodzi przez ten sam weryfikator zdań co odpowiedzi.
Krótkie dokumenty idą do modelu w całości. Dłuższe (skrypt, rozdział podręcznika) — w częściach, a wynik każdej części
ma odwołania do jej fragmentów. Z bardzo długich (ustawy) albo gdy podano temat — fragmenty pasujące do tematu.
"""
from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

from .core import REFUSAL_TEXT, Answer, Sentence, Source, _cites, is_refusal, split_sentences
from .labels import legal_label, superscripts

_INTRO = re.compile(r"^\W*(poniżej|oto|przedstawiam|notatka|podsumowanie|streszczenie|słowniczek|pytania|fiszki)\b", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•–]|\d{1,2}[.)])\s+")
_QA = re.compile(r"^\s*P(?:ytanie)?\s*:\s*(.+?)\s*\|\s*O(?:dpowiedź)?\s*:\s*(.+)$", re.I)
MAX_FULL_CHUNKS = 24      # ok. 15 tys. znaków na część — mieści się w kontekście modelu razem z odpowiedzią
MAX_PARTS = 6             # do ok. 140 fragmentów (ok. 60 stron) bez podawania tematu
TOPIC_K = 8

SYSTEM = ("Jesteś starannym asystentem. Pracujesz wyłącznie na podanych fragmentach dokumentów, po polsku. "
          "Każde zdanie albo wiersz kończysz odwołaniem w nawiasie kwadratowym do numeru fragmentu, np. [2]. "
          "Nie dodajesz wiedzy spoza fragmentów, nie zgadujesz i nie dajesz własnych rad. Zachowujesz warunki i wyjątki "
          "(np. „w jedną stronę”, „chyba że…”, kogo i czego dotyczy zasada). Gdy fragmenty nie zawierają potrzebnych "
          "informacji, odpowiadasz dokładnie: BRAK_ODPOWIEDZI. Numer w nawiasie [n] to numer fragmentu z nagłówka „[n]” "
          "— numery rozdziałów, punktów i paragrafów w tekście (np. „6.”, „§ 6”) to nie są numery fragmentów.")

LENGTH = {"short": "3–4", "standard": "5–8", "long": "10–14"}
LINES = "Każda pozycja w osobnym wierszu zaczynającym się od „- ”. Bez nagłówków i bez wstępu."
SPREAD = " Rozłóż pozycje na wszystkie części tekstu, także środkowe i końcowe (wyjątki, terminy, uwagi praktyczne)."

TOOLS = {
    "summary": {
        "name": "Streszczenie",
        "kind": "prose",
        "prompt": ("Streść fragmenty w {n} zdaniach{about}. {first}Potem najważniejsze myśli, zasady, liczby i terminy. "
                   "Bez wstępu typu „oto streszczenie”. Każde zdanie zakończ odwołaniem [n]." + SPREAD),
        "prompt_points": ("Streść fragmenty w {n} punktach{about}: najważniejsze myśli, zasady, liczby i terminy. " + LINES +
                          " Każdy punkt to jedno pełne zdanie zakończone odwołaniem [n]." + SPREAD),
    },
    "facts": {
        "name": "Terminy, kwoty i obowiązki",
        "kind": "lines",
        "prompt": ("Wypisz z fragmentów{about} terminy, daty, kwoty, liczby, limity i obowiązki — najwyżej 20 pozycji, "
                   "najważniejsze najpierw. Każda pozycja to jedno pełne zdanie zrozumiałe bez reszty tekstu: kto albo co, "
                   "liczba albo termin i warunek, np. „- Rozliczenie podróży składa się w ciągu 14 dni od jej zakończenia [2]”. "
                   + LINES + " Przepisuj liczby dokładnie tak, jak są we fragmentach."),
    },
    "memo": {
        "name": "Notatka",
        "kind": "prose",
        "needs_topic": True,
        "prompt": ("Napisz krótką notatkę na temat: {topic}. Bez tytułu i bez zdań typu „poniżej przedstawiam”. "
                   "Najpierw jedno zdanie: czego dotyczy temat, potem 3–6 punktów z najważniejszymi ustaleniami — tylko to, "
                   "co jest zapisane we fragmentach, bez własnych wniosków i zaleceń. Każde zdanie i każdy punkt zakończ "
                   "odwołaniem [n]. Jeśli fragmenty nie dotyczą tego tematu, odpowiedz BRAK_ODPOWIEDZI."),
    },
    "quiz": {
        "name": "Pytania sprawdzające",
        "kind": "qa",
        "prompt": ("Ułóż {q} pytań sprawdzających wiedzę z fragmentów{about} (do nauki albo szkolenia). Każde pytanie ma "
                   "krótką odpowiedź, którą da się znaleźć wprost we fragmencie. Format, jeden wiersz na pytanie: "
                   "„P: pytanie? | O: odpowiedź [n]”. Odpowiedź ma wprost i w całości odpowiadać na pytanie (nie sam przykład). "
                   "Bez nagłówków i bez wstępu. Nie pytaj o rzeczy, których nie ma we fragmentach." + SPREAD),
    },
    "glossary": {
        "name": "Słowniczek pojęć",
        "kind": "lines",
        "prompt": ("Wypisz najważniejsze pojęcia z fragmentów{about} — najwyżej 15 — z krótką definicją albo wyjaśnieniem "
                   "opartym tylko na fragmentach, w formacie: „- pojęcie — wyjaśnienie [n]”. Pojęcie to nazwa, termin albo skrót "
                   "(1–4 słowa), nie cała zasada. " + LINES),
    },
    "claims": {
        "name": "Tezy, argumenty i ograniczenia",
        "kind": "lines",
        "prompt": ("Wydobądź z fragmentów{about} główne tezy, argumenty albo dane, które je wspierają, oraz wskazane "
                   "ograniczenia lub wyjątki — najwyżej 12 pozycji. Nie oceniaj tekstu od siebie. Każdy wiersz MUSI zaczynać się "
                   "od jednego z oznaczeń: „- Teza: …”, „- Argument: …” albo „- Ograniczenie: …” i kończyć odwołaniem [n]. "
                   + LINES + SPREAD),
    },
    "simple": {
        "name": "Wyjaśnij prościej",
        "kind": "prose",
        "prompt": ("Wyjaśnij treść fragmentów{about} prostym językiem, jak komuś bez wiedzy specjalistycznej: krótkie zdania, "
                   "codzienne słowa, trudne terminy objaśnione w nawiasie. {n} zdań. Nie dodawaj przykładów ani rad spoza "
                   "fragmentów. Każde zdanie zakończ odwołaniem [n]."),
    },
}

QUIZ_N = {"short": 5, "standard": 8, "long": 12}
MAX_ITEMS = {"short": 4, "standard": 8, "long": 14}  # górna granica zdań streszczenia — model czasem ją przekracza


def _sources_from_chunks(chunks, start=1):
    return [Source(n=i, text=superscripts(m["text"]), file=m["file"], locator=f"lines {m['start_line']}-{m['end_line']}",
                   label=legal_label(m["file"], m["start_line"], m["text"])) for i, m in enumerate(chunks, start)]


def gather_parts(index, doc_ids, topic: str = ""):
    """Fragmenty do narzędzia: [części], opis. Część = lista źródeł; numeracja [n] ciągła przez wszystkie części."""
    files = [p for p in (index.file_by_id(str(i)) for i in (doc_ids or [])) if p is not None]
    if not files:
        files = sorted({Path(m["file"]) for m in index.meta})
    wanted = {str(f) for f in files}
    chunks = [m for m in index.meta if m["file"] in wanted]
    if not topic.strip() and chunks:
        if len(chunks) > MAX_FULL_CHUNKS * MAX_PARTS:
            raise ValueError("Wybrane dokumenty są za długie, żeby przetworzyć je w całości. Zaznacz po lewej jeden "
                             "dokument (np. „Regulamin pracy”) albo wpisz temat (np. „urlop wypoczynkowy”) — wtedy "
                             "Sejf weźmie pasujące fragmenty.")
        order = {str(f): k for k, f in enumerate(files)}
        chunks.sort(key=lambda m: (order.get(m["file"], 0), m["start_line"]))
        src = _sources_from_chunks(chunks)
        n_parts = -(-len(src) // MAX_FULL_CHUNKS)
        size = -(-len(src) // n_parts)  # równe części
        parts = [src[i:i + size] for i in range(0, len(src), size)]
        what = "cały dokument" if len(files) == 1 else f"całe dokumenty ({len(files)})"
        return parts, what + (f", w {len(parts)} częściach" if len(parts) > 1 else "")
    if not topic.strip():
        return [], "brak dokumentów"
    prev = index.only_files
    index.only_files = wanted
    try:
        hits = index.search(topic, TOPIC_K)
    finally:
        index.only_files = prev
    src = [Source(n=i, text=superscripts(h["snippet"]), file=h["file"], locator=h["locator"],
                  label=legal_label(h["file"], h["start_line"], h["snippet"]), rerank=h.get("rerank_score"))
           for i, h in enumerate(hits, 1)]
    return ([src] if src else []), f"fragmenty pasujące do tematu „{topic.strip()}”"


def gather_sources(index, doc_ids, topic: str = ""):
    """Zgodność wsteczna: wszystkie źródła jako jedna lista."""
    parts, scope = gather_parts(index, doc_ids, topic)
    return [s for p in parts for s in p], scope


def build_messages(tool: str, sources, topic: str = "", opts: dict | None = None, parts: int = 1):
    opts = opts or {}
    t = TOOLS[tool]
    length = opts.get("length") if opts.get("length") in LENGTH else "standard"
    n = LENGTH[length]
    if parts > 1 and tool in ("summary", "simple"):  # przy kilku częściach każda krócej
        n = {"short": "2–3", "standard": "3–5", "long": "6–8"}[length]
    q = QUIZ_N[length]
    if parts > 1 and tool == "quiz":
        q = max(3, -(-q // parts))
    about = f", w zakresie tematu: {topic.strip()}" if topic.strip() else ""
    prompt = t["prompt_points"] if (tool == "summary" and opts.get("form") == "points") else t["prompt"]
    first = "Pierwsze zdanie: czego dotyczy tekst. " if parts == 1 else ""
    task = prompt.format(topic=topic.strip() or "najważniejsze informacje z dokumentów", n=n, q=q, about=about, first=first)
    blocks = [f"[{s.n}] {s.label}\n{s.text}" for s in sources]
    user = "Fragmenty dokumentów:\n\n" + "\n\n".join(blocks) + f"\n\nZadanie: {task}"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


def parse_lines(raw: str):
    """Wynik w wierszach: jeden wiersz = jedna pozycja (z odwołaniem). Nagłówki i wstępy bez odwołań pomijane."""
    out = []
    for line in re.sub(r"\*\*|__|^#+\s*", "", raw or "", flags=re.M).splitlines():
        line = _BULLET.sub("", line).strip()
        if not line:
            continue
        cited = _cites(line)
        if not cited and (len(line) < 90 or _INTRO.match(line)):
            continue
        out.append(Sentence(text=line, cited=cited))
    return out


def parse_prose(raw: str):
    return [s for s in split_sentences(raw) if s.cited or (len(s.text) > 90 and not _INTRO.match(s.text))]


def _probe(it, kind):
    """Twierdzenie do weryfikacji: zdanie albo (dla fiszek) pytanie + odpowiedź razem."""
    if kind != "qa":
        return Sentence(text=it.text, cited=list(it.cited))
    m = _QA.match(it.text)
    return Sentence(text=f"{m.group(1)} {m.group(2)}", cited=list(it.cited)) if m else None


def _verify(sejf, items, part_of, kind):
    """Weryfikacja zdań; gdy zdanie nie ma potwierdzenia w cytowanym fragmencie, sprawdzamy pozostałe fragmenty tej
    samej części. Model 4B często cytuje sąsiedni fragment — wtedy poprawiamy numer na fragment, który zdanie potwierdza,
    i oznaczamy to (renumbered). Zwraca (pozycje, indeksy pozycji z poprawionym numerem)."""
    keep, probes = [], []
    for it in items:
        pr = _probe(it, kind)
        if pr is not None:
            keep.append(it)
            probes.append(pr)
    by_part = {}
    for it, pr in zip(keep, probes):
        by_part.setdefault(id(part_of[id(it)]), (part_of[id(it)], []))[1].append(pr)
    for part, prs in by_part.values():
        sejf._verify(prs, part)
    fixed = []
    for k, (it, pr) in enumerate(zip(keep, probes)):
        if pr.status == "unsupported" and it.cited:
            part = part_of[id(it)]
            alt = Sentence(text=pr.text, cited=[x.n for x in part if x.n not in it.cited])
            if alt.cited:
                sejf._verify([alt], part)
                if alt.status == "supported" and alt.best_source is not None:
                    it.cited = [alt.best_source]
                    pr = alt
                    fixed.append(k)
        it.support, it.status, it.best_source = pr.support, pr.status, pr.best_source
    return keep, fixed


def _cap(tool, opts, parts):
    """Najwyżej tyle pozycji, ile obiecuje wybrana opcja (na jedną część)."""
    length = opts.get("length") if opts.get("length") in LENGTH else "standard"
    if tool == "quiz":
        q = QUIZ_N[length]
        return q if parts == 1 else max(3, -(-q // parts))
    if tool in ("summary", "simple"):
        m = MAX_ITEMS[length]
        return m if parts == 1 else {"short": 3, "standard": 5, "long": 8}[length]
    return 25


def run_tool(sejf, index, generate_long, tool: str, doc_ids=None, topic: str = "", user: str = "local",
             opts: dict | None = None) -> dict:
    if tool not in TOOLS:
        raise ValueError("Nieznane narzędzie.")
    t = TOOLS[tool]
    if t.get("needs_topic") and not topic.strip():
        raise ValueError("Wpisz temat notatki.")
    opts = {k: str(v) for k, v in (opts or {}).items() if k in ("length", "form")}
    t0 = time.perf_counter()
    parts, scope = gather_parts(index, doc_ids, topic)
    sources = [s for p in parts for s in p]
    for s in sources:
        s.sha256 = hashlib.sha256(s.text.encode("utf-8")).hexdigest()
    title = t["name"] + (f": {topic.strip()}" if topic.strip() else "")
    if not sources:
        ans = Answer(title, "no_sources", REFUSAL_TEXT, timings={"retrieval_s": time.perf_counter() - t0})
        sejf._audit(ans, user)
        return {**ans.to_dict(), "tool": tool, "scope": scope, "opts": opts}
    kind = "lines" if (tool == "summary" and opts.get("form") == "points") else t["kind"]
    t1 = time.perf_counter()
    raws, items, part_of = [], [], {}
    for k, part in enumerate(parts):
        raw = generate_long(build_messages(tool, part, topic, opts, parts=len(parts)))
        raws.append(raw)
        if is_refusal(raw):
            continue
        got = parse_prose(raw) if kind == "prose" else parse_lines(raw)
        allowed = {s.n for s in part}
        for it in got:  # odwołanie spoza tej części = model pomylił numer; zostawiamy, weryfikator to oznaczy
            it.cited = [c for c in it.cited if c in allowed] or it.cited
        got = got[:_cap(tool, opts, len(parts))]
        for it in got:
            part_of[id(it)] = part
        items += got
    t2 = time.perf_counter()
    raw_all = "\n\n".join(raws)
    fixed = []
    if not items:
        ans = Answer(title, "refused", REFUSAL_TEXT, sources=sources, raw=raw_all,
                     timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1})
    else:
        items, fixed = _verify(sejf, items, part_of, kind)
        t3 = time.perf_counter()
        ans = Answer(title, "answered", " ".join(s.text for s in items), sentences=items, sources=sources, raw=raw_all,
                     timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1, "verify_s": t3 - t2})
        if not items:
            ans.status, ans.text = "refused", REFUSAL_TEXT
    sejf._audit(ans, user)
    d = {**ans.to_dict(), "tool": tool, "kind": kind, "scope": scope, "opts": opts, "parts": len(parts)}
    if ans.status == "answered":
        for k in fixed:
            d["sentences"][k]["renumbered"] = True
    return d
