"""Sejf: odpowiedzi z dokumentów z cytatami i weryfikacją każdego zdania.

Przepływ:
  1. retriever(query, k) -> fragmenty (już przefiltrowane uprawnieniami użytkownika)
  2. generator(messages) -> odpowiedź Bielika z odwołaniami [n]
  3. podział na zdania, weryfikator(zdanie, źródło) -> P(poparte)
  4. polityka: 'flag' (oznacz) albo 'strict' (usuń niepotwierdzone)
  5. dziennik audytu (hashe, wersje modeli, PII zamaskowane)

Moduł nie zależy od LocalDocs ani od llama.cpp - komponenty są wstrzykiwane,
dzięki czemu ten sam kod działa w aplikacji i w ewaluacji na Kaggle.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable

from . import pii

REFUSAL_TOKEN = "BRAK_ODPOWIEDZI"
REFUSAL_TEXT = "Nie znaleziono odpowiedzi w dostępnych dokumentach."

SYSTEM_PROMPT = (
    "Jesteś asystentem, który odpowiada WYŁĄCZNIE na podstawie podanych fragmentów dokumentów. "
    "Zasady:\n"
    "1. Każde zdanie odpowiedzi zakończ odwołaniem do źródła w nawiasie kwadratowym, np. [2] lub [1][3].\n"
    "2. Nie dodawaj wiedzy spoza fragmentów. Nie zgaduj liczb, terminów ani kwot.\n"
    f"3. Jeśli fragmenty nie zawierają odpowiedzi, napisz dokładnie: {REFUSAL_TOKEN}\n"
    "4. Odpowiadaj po polsku, zwięźle (najwyżej 5 zdań)."
)


@dataclass
class Source:
    n: int
    text: str
    file: str = ""
    locator: str = ""
    label: str = ""          # np. "Kodeks pracy, art. 152"
    score: float = 0.0
    sha256: str = ""
    rerank: float | None = None   # ocena cross-encodera (0-1), jeśli reranker włączony


@dataclass
class Sentence:
    text: str
    cited: list
    support: float | None = None
    status: str = "unchecked"   # supported | unsupported | uncited | unchecked
    best_source: int | None = None


@dataclass
class Answer:
    question: str
    status: str                 # answered | refused | no_sources
    text: str
    sentences: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    timings: dict = field(default_factory=dict)
    raw: str = ""
    removed: int = 0

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------- zdania
_ABBR = r"(?:art|ust|pkt|lit|poz|nr|np|tj|tzw|zm|r|ww|al|godz|min|zł|ok|m\.in|Dz\.U|Dz|U|par|cz|rozdz|tys|mln|wg|św|im|s)"
_SPLIT = re.compile(r"(?<=[.!?])(?:\[\d+\])*\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ\d„\"(])")
_CIT = re.compile(r"\[(\d{1,2}(?:\s*,\s*\d{1,2})*)\]")  # [1], [1][2], [1, 2]


def _cites(fragment: str):
    return [int(x) for g in _CIT.findall(fragment) for x in re.findall(r"\d{1,2}", g)]


def split_sentences(text: str):
    """Dzieli odpowiedź na zdania, nie tnąc po skrótach prawniczych (art., ust., pkt, §).
    Markdown modelu (**Odpowiedź:**, nagłówki-pytania) usuwany; wiersz = granica zdania; nagłówki nie są twierdzeniami."""
    DOT = "\u2024"
    text = re.sub(r"\*\*|__|^#+\s*", "", (text or "").strip(), flags=re.M)
    out = []
    for line in text.splitlines():
        line = re.sub(r"^\s*[-*•]\s+", "", line).strip()
        if not line:
            continue
        # nagłówek: krótki wiersz kończący się ":" albo "?" bez odwołania [n] - pomijamy
        if len(line) < 80 and re.search(r"[:?]\s*$", line) and not _CIT.search(line):
            continue
        # wyliczenia "1." / "2a." / "§ 1." na początku wiersza nie kończą zdania
        line = re.sub(r"^(§\s*\d+[a-z]*|\d{1,3}[a-z]?)\.(?=\s)", lambda m: m.group(1) + DOT, line)
        protected = re.sub(rf"\b({_ABBR})\.", lambda m: m.group(1) + DOT, line, flags=re.I)
        # cytaty "[1]." / "[1, 2]." za kropką - przesuń przed kropkę, żeby należały do zdania
        protected = re.sub(r"\.\s*((?:\[\d{1,2}(?:\s*,\s*\d{1,2})*\])+)", r"\1.", protected)
        for p in _SPLIT.split(protected):
            p = p.replace(DOT, ".").strip()
            if p:
                out.append(Sentence(text=p, cited=_cites(p)))
    return out


_META = re.compile(r"^\W*(\*\*)?(odpowied[źz]|brak (innych|bezpośredniego|informacji|odniesienia)|w podanych fragmentach|fragmenty nie|na podstawie (podanych|powyższych) fragmentów nie)", re.I)


_QUOTE = re.compile(r'["„“”«]([^"„“”«»]{20,})["“”»]')


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("\u00ad", "")).strip().lower()


def _verbatim_quote(claim: str, sources) -> int | None:
    """Zdanie będące dosłownym cytatem źródła (np. 'Art. 154 § 2: "Wymiar urlopu wynosi: 26 dni..."') jest potwierdzone
    bez modelu: NLI zaniża takie zdania przez prefiks z numerem przepisu. Poza cudzysłowem dopuszczamy tylko
    krótki opis miejsca (≤ 6 słów), żeby cytat nie „uwiarygodniał” dopisanego twierdzenia."""
    quotes = _QUOTE.findall(claim)
    if not quotes:
        return None
    rest = _QUOTE.sub(" ", claim)
    if len(re.findall(r"[^\W\d_]{2,}", rest)) > 6:
        return None
    for src in sources:
        body = _norm(src.text)
        if all(_norm(q).rstrip(".;, ") in body for q in quotes):
            return src.n
    return None


def strip_citations(s: str) -> str:
    return re.sub(r"\s*\[\d{1,2}(?:\s*,\s*\d{1,2})*\]", "", s).strip()


# ---------------------------------------------------------------- prompt
def build_messages(question: str, sources: list[Source], max_chars_per_source: int = 1400):
    blocks = []
    for s in sources:
        head = f"[{s.n}] {s.label}" if s.label else f"[{s.n}]"
        blocks.append(f"{head}\n{s.text[:max_chars_per_source]}")
    user = "Fragmenty dokumentów:\n\n" + "\n\n".join(blocks) + f"\n\nPytanie: {question}"
    return [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]


def is_refusal(text: str) -> bool:
    # Bielik v3 w llama.cpp czasem gubi literę ("BRAK_ODPOIEDZI") - dopuszczamy zniekształcenia znacznika
    t = text.strip()
    return bool(re.match(r"^\W*BRAK[_ ]?ODP\w{0,10}\b", t, re.I)) or REFUSAL_TOKEN in t[:200]


# ---------------------------------------------------------------- pipeline
class Sejf:
    def __init__(self,
                 retriever: Callable[[str, int], list[Source]],
                 generator: Callable[[list], str],
                 verifier: Callable[[list[tuple[str, str]]], list[float]] | None = None,
                 threshold: float = 0.5,
                 mode: str = "flag",
                 k: int = 5,
                 min_retrieval_score: float | None = None,
                 min_rerank_score: float | None = None,
                 audit_path: str | Path | None = None,
                 model_info: dict | None = None):
        self.retriever = retriever
        self.generator = generator
        self.verifier = verifier
        self.threshold = threshold
        self.mode = mode
        self.k = k
        self.min_retrieval_score = min_retrieval_score
        # bramka odmowy: gdy najlepszy fragment ma niską ocenę rerankera, odpowiedni przepis zwykle nie został znaleziony
        # i model zgaduje. Próg 0.9 wybrany na zbiorze (a) (pierwszy, przy którym żadne pytanie-pułapka nie przechodzi).
        self.min_rerank_score = min_rerank_score
        self.audit_path = Path(audit_path) if audit_path else None
        self.model_info = model_info or {}

    def ask(self, question: str, user: str = "", mode: str | None = None) -> Answer:
        mode = mode or self.mode
        t0 = time.perf_counter()
        sources = self.retriever(question, self.k)
        for i, s in enumerate(sources, 1):
            s.n = i
            s.sha256 = s.sha256 or hashlib.sha256(s.text.encode("utf-8")).hexdigest()
        t1 = time.perf_counter()
        reranked = [s.rerank for s in sources if s.rerank is not None]
        if not sources or (self.min_retrieval_score is not None
                           and max(s.score for s in sources) < self.min_retrieval_score) \
                or (self.min_rerank_score is not None and reranked and max(reranked) < self.min_rerank_score):
            ans = Answer(question, "no_sources", REFUSAL_TEXT, sources=sources,
                         timings={"retrieval_s": t1 - t0})
            self._audit(ans, user)
            return ans

        raw = self.generator(build_messages(question, sources))
        t2 = time.perf_counter()
        if is_refusal(raw):
            ans = Answer(question, "refused", REFUSAL_TEXT, sources=sources, raw=raw,
                         timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1})
            self._audit(ans, user)
            return ans

        sents = split_sentences(raw)
        self._verify(sents, sources)
        t3 = time.perf_counter()

        kept = sents
        removed = 0
        if mode == "strict" and self.verifier is not None:
            # tryb ścisły: zostaje tylko to, co ma odwołanie [n] I zostało potwierdzone w tym źródle
            kept = [s for s in sents if s.status == "supported"]
            removed = len(sents) - len(kept)
        if not kept:
            ans = Answer(question, "refused", REFUSAL_TEXT, sentences=sents, sources=sources, raw=raw,
                         removed=removed,
                         timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1, "verify_s": t3 - t2})
            self._audit(ans, user)
            return ans
        text = " ".join(s.text for s in kept)
        ans = Answer(question, "answered", text, sentences=sents, sources=sources, raw=raw, removed=removed,
                     timings={"retrieval_s": t1 - t0, "generation_s": t2 - t1, "verify_s": t3 - t2})
        self._audit(ans, user)
        return ans

    def _verify(self, sents: list[Sentence], sources: list[Source]):
        if self.verifier is None:
            return
        by_n = {s.n: s for s in sources}
        pairs, owners = [], []
        for i, s in enumerate(sents):
            claim = strip_citations(s.text)
            if len(re.findall(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]", claim)) < 3:
                continue  # obrywek listy / sama interpunkcja ("1.7)].") - nie jest twierdzeniem
            if _META.match(claim):
                s.status, s.support = "unsupported", 0.0  # komentarz o źródłach zamiast odpowiedzi
                continue
            # krótkie zdania ("7 dni.", "Tak.") też weryfikujemy: w prawie to najgroźniejsze błędy
            cands = [n for n in s.cited if n in by_n] or list(by_n)
            hit = _verbatim_quote(claim, [by_n[n] for n in cands])
            if hit is not None:
                s.status, s.support, s.best_source = ("supported" if s.cited else "uncited"), 1.0, hit
                continue
            for n in cands:
                pairs.append((claim, by_n[n].text))
                owners.append((i, n))
        if not pairs:
            return
        probs = self.verifier(pairs)
        best = {}
        for (i, n), p in zip(owners, probs):
            if i not in best or p > best[i][0]:
                best[i] = (float(p), n)
        for i, (p, n) in best.items():
            s = sents[i]
            s.support, s.best_source = p, n
            if p >= self.threshold:
                s.status = "supported" if s.cited else "uncited"
            else:
                s.status = "unsupported"

    def _audit(self, ans: Answer, user: str):
        if not self.audit_path:
            return
        q_masked, q_pii = pii.mask(ans.question)
        rec = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "user": user,
            "question_masked": q_masked,
            "question_sha256": hashlib.sha256(ans.question.encode("utf-8")).hexdigest(),
            "pii_in_question": q_pii,
            "status": ans.status,
            "answer_sha256": hashlib.sha256(ans.text.encode("utf-8")).hexdigest(),
            "sources": [{"n": s.n, "file": s.file, "locator": s.locator, "sha256": s.sha256} for s in ans.sources],
            "sentences": [{"status": s.status, "support": s.support, "cited": s.cited} for s in ans.sentences],
            "removed": ans.removed,
            "models": self.model_info,
            "timings": {k: round(v, 3) for k, v in ans.timings.items()},
        }
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        prev = ""
        if self.audit_path.exists():
            # łańcuch hashy: każdy wpis zawiera hash poprzedniego (wykrywanie edycji dziennika)
            with open(self.audit_path, "rb") as f:
                try:
                    f.seek(-65536, 2)
                except OSError:
                    f.seek(0)
                tail = f.read().splitlines()
                if tail:
                    prev = hashlib.sha256(tail[-1]).hexdigest()
        rec["prev_sha256"] = prev
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def verify_audit_chain(path: str | Path):
    """Sprawdza łańcuch hashy dziennika. Zwraca (ok, numer_pierwszej_złej_linii|None)."""
    lines = Path(path).read_bytes().splitlines()
    prev = ""
    for i, line in enumerate(lines, 1):
        rec = json.loads(line)
        if rec.get("prev_sha256", "") != prev:
            return False, i
        prev = hashlib.sha256(line).hexdigest()
    return True, None
