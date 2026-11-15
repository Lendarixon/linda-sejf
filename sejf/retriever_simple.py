"""Samodzielna wyszukiwarka Sejfu (wersja open source, bez Linda Probe).

Hybryda: znaczeniowa (multilingual-e5-small, ONNX) + słowna (SQLite FTS5, BM25), łączone RRF,
potem polski reranker (sdadas/polish-reranker-base-ranknet, ONNX, sigmoid) ocenia 30 najlepszych.
Ocena rerankera trafia do bramki odmowy Sejfu (min_rerank_score, domyślnie 0,9).

Indeks jest zapisywany w <state>/index_<hash>.npz/.json i odbudowywany, gdy pliki się zmienią.
Obsługiwane pliki: .txt, .md, .odt, .rtf, .html/.htm, .epub, .pptx, .xlsx oraz .pdf i .docx (pypdf / python-docx).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

import numpy as np

from .core import Source
from .extract import SUPPORTED_EXT, TEXT_EXT, read_text as _extract_text
from .labels import legal_label, superscripts

_MIN_CHUNK = 150


# ------------------------------------------------------------------ pliki i fragmenty
def read_text(p: Path) -> str:
    return _extract_text(p)


def _chunks_raw(text: str):
    """Okna do 35 wierszy / ~650 znaków z zakładką 2 wierszy; długie wiersze cięte co 800 znaków."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        j, size = i, 0
        while j < len(lines) and j - i < 35 and (size < 650 or j == i):
            size += len(lines[j]) + 1
            j += 1
        content = "\n".join(lines[i:j])
        if content.strip():
            for off in range(0, len(content), 800):
                part = content[off:off + 800]
                first = i + 1 + content[:off].count("\n")
                yield {"start_line": first, "end_line": first + part.count("\n"), "text": part}
        i = j if j - i <= 2 else j - 2


def chunks(text: str):
    """Drobne resztki (< 150 znaków) doklejane do poprzedniego fragmentu."""
    pending = None
    for m in _chunks_raw(text):
        if pending is None:
            pending = m
            continue
        if len(m["text"]) < _MIN_CHUNK and len(pending["text"]) + len(m["text"]) + 1 <= 1000:
            pending["text"] += "\n" + m["text"]
            pending["end_line"] = max(pending["end_line"], m["end_line"])
            continue
        yield pending
        pending = m
    if pending is not None:
        yield pending


def windows(text: str, max_chars: int = 380, step: int = 2):
    """Krótkie okna (zwykle ustęp lub punkt) do oceny rerankerem: kolejne wiersze do ~380 znaków, start co 2 wiersze.
    'context' = okno + 1 wiersz przed i po (to trafia do modelu); ctx_start = numer pierwszego wiersza kontekstu w fragmencie."""
    lines = text.split("\n")
    out, seen = [], set()
    for a in range(0, len(lines), step):
        b, size = a, 0
        while b < len(lines) and (size < max_chars or b == a):
            size += len(lines[b]) + 1
            b += 1
        if (a, b) in seen or not "".join(lines[a:b]).strip():
            continue
        seen.add((a, b))
        ca, cb = max(0, a - 1), min(len(lines), b + 1)
        out.append({"text": "\n".join(lines[a:b]), "context": "\n".join(lines[ca:cb]), "ctx_start": ca})
        if b >= len(lines):
            break
    return out


# ------------------------------------------------------------------ modele ONNX
class _Onnx:
    def __init__(self, d: Path, threads: int, max_length: int, pair: bool):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        self.tok = Tokenizer.from_file(str(d / "tokenizer.json"))
        self.tok.enable_truncation(max_length=max_length, strategy="longest_first" if pair else "longest_first")
        pid = self.tok.token_to_id("<pad>")
        pid = 1 if pid is None else pid
        self.tok.enable_padding(pad_id=pid, pad_token=self.tok.id_to_token(pid) or "<pad>")
        so = ort.SessionOptions()
        so.intra_op_num_threads = threads
        self.sess = ort.InferenceSession(str(d / "model.onnx"), so, providers=["CPUExecutionProvider"])

    def run(self, batch):
        enc = self.tok.encode_batch(batch)
        ids = np.array([e.ids for e in enc], dtype=np.int64)
        mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
        return self.sess.run(None, {"input_ids": ids, "attention_mask": mask})[0], mask


class Embedder:
    def __init__(self, d: Path, threads: int = 4):
        self.m = _Onnx(d, threads, 512, False)

    def __call__(self, texts, batch: int = 32, progress=None):
        """Wektory tekstów. Teksty liczone w kolejności długości (mniej dopełniania w partii = szybciej na CPU),
        wynik w kolejności wejścia. progress(gotowe, wszystkie) po każdej partii; wyjątek z progress przerywa liczenie."""
        if not len(texts):
            return np.zeros((0, 384), np.float32)
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        out = np.zeros((len(texts), 384), np.float32)
        for i in range(0, len(order), batch):
            idx = order[i:i + batch]
            h, mask = self.m.run([texts[j] for j in idx])
            mask = mask[..., None].astype(np.float32)
            v = (h * mask).sum(1) / np.clip(mask.sum(1), 1e-9, None)
            out[idx] = v / np.linalg.norm(v, axis=1, keepdims=True)
            if progress:
                progress(min(i + batch, len(order)), len(order))
        return out


class Reranker:
    def __init__(self, d: Path, threads: int = 4):
        self.m = _Onnx(d, threads, 256, True)

    def __call__(self, query: str, texts, batch: int = 16):
        s = []
        for i in range(0, len(texts), batch):
            logits, _ = self.m.run([(query, t) for t in texts[i:i + batch]])
            s.extend((1 / (1 + np.exp(-logits.reshape(-1)))).tolist())
        return s


# ------------------------------------------------------------------ indeks i wyszukiwanie
_WORD = re.compile(r"\w+", re.U)


class Index:
    def __init__(self, folder, models_dir, state_dir, threads: int = 4, rerank_n: int = 30, depth: int = 60,
                 passages: bool = False, passage_top: int = 15, progress=None):
        self.passages, self.passage_top = passages, passage_top
        self.only_files = None  # zbiór pełnych ścieżek plików, do których zawęża się wyszukiwanie (wybór źródeł w UI)
        self.gen = 0
        self.pending_vectors = []
        self.folder = Path(folder)
        self.models = Path(models_dir)
        self.state = Path(state_dir)
        self.state.mkdir(parents=True, exist_ok=True)
        self.rerank_n, self.depth = rerank_n, depth
        self.emb = Embedder(self.models / "e5", threads)
        self.rr = Reranker(self.models / "reranker", threads)
        self._build(progress)

    def _files(self):
        return sorted(p for p in self.folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXT and not p.name.startswith(("~$", ".")))

    def _cache_path(self, p: Path) -> Path:
        st = p.stat()
        key = hashlib.sha256(f"{p}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:20]
        return self.state / "files" / f"{key}.npz"

    def _load_cache(self, p: Path):
        cache = self._cache_path(p)
        if not cache.exists():
            return None
        z = np.load(cache, allow_pickle=False)
        meta = json.loads(str(z["meta"]))
        vec = z["v"]
        if len(vec) != len(meta):
            return None
        return meta, vec

    def save_cache(self, p: Path, meta, vec):
        """Zapisuje kompletny cache fragmentów i wektorów pliku (.npz)."""
        cache = self._cache_path(p)
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, v=vec.astype(np.float32), meta=np.array(json.dumps(meta, ensure_ascii=False)))

    def prepare_text(self, p):
        """Odczytuje tekst i dzieli go na fragmenty bez liczenia wektorów e5 (szybkie, pod BM25)."""
        p = Path(p)
        meta = []
        for c in chunks(read_text(p)):
            c["file"] = str(p)
            meta.append(c)
        return meta

    def embed_meta(self, p: Path, meta, progress=None):
        """Liczy wektory e5 dla podanych fragmentów pliku (bez zmiany indeksu)."""
        if not meta:
            return np.zeros((0, 384), np.float32)
        p = Path(p)
        return self.emb(["passage: " + p.stem + "\n" + m["text"] for m in meta], progress=progress).astype(np.float32)

    def _file_part(self, p: Path, progress=None):
        """Fragmenty i wektory jednego pliku; pamięć podręczna per plik (ścieżka + rozmiar + data zmiany)."""
        cached = self._load_cache(p)
        if cached is not None:
            return cached
        meta = self.prepare_text(p)
        vec = self.embed_meta(p, meta, progress=progress)
        self.save_cache(p, meta, vec)
        return meta, vec

    def _build(self, progress=None, folder=None):
        """Buduje indeks folderu (pliki z pamięci podręcznej wczytywane od razu, nowe — tylko tekstowo do policzenia w tle).
        Gotowy indeks (razem z folderem) podmieniany jest naraz, więc w trakcie przebudowy działa stary."""
        folder = Path(folder) if folder is not None else self.folder
        files = sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXT
                       and not p.name.startswith(("~$", ".")))
        meta, vecs, masks, pending = [], [], [], []
        for k, p in enumerate(files, 1):
            try:
                cached = self._load_cache(p)
                if cached is not None:
                    m, v = cached
                    mask = np.ones(len(m), dtype=bool)
                else:
                    m = self.prepare_text(p)
                    v = np.zeros((len(m), 384), np.float32)
                    mask = np.zeros(len(m), dtype=bool)
                    if m:
                        pending.append(p)
            except Exception:  # plik nieczytelny / zablokowany — pomijamy, nie przerywamy całości
                m, v, mask = [], np.zeros((0, 384), np.float32), np.zeros(0, dtype=bool)
            meta += m
            if len(m):
                vecs.append(v)
                masks.append(mask)
            if progress:
                progress(k, len(files), p.name)
        vec = np.vstack(vecs) if vecs else np.zeros((0, 384), np.float32)
        has_vec = np.concatenate(masks) if masks else np.zeros(0, dtype=bool)
        db = sqlite3.connect(":memory:", check_same_thread=False)
        db.execute("CREATE VIRTUAL TABLE docs USING fts5(text, tokenize='unicode61')")
        db.executemany("INSERT INTO docs(rowid, text) VALUES (?, ?)", ((i, m["text"].lower()) for i, m in enumerate(meta)))
        self.gen += 1
        self.meta, self.vec, self.has_vec, self.db, self.folder = meta, vec, has_vec, db, folder
        self.only_files = None
        self.pending_vectors = pending
        return pending

    def reload(self, folder=None, progress=None):
        """Zmiana folderu dokumentów albo odświeżenie (nowe, zmienione i usunięte pliki). Zwraca pliki bez cache."""
        return self._build(progress, folder)

    def prepare_file(self, p, progress=None):
        """Fragmenty i wektory nowego pliku — bez zmiany indeksu (można liczyć w tle, bez blokady)."""
        return self._file_part(Path(p), progress)

    def add_file(self, p) -> int:
        """Dodaje nowy plik do działającego indeksu (bez przebudowy całości). Zwraca liczbę fragmentów."""
        return self.commit_file(*self.prepare_file(p))

    def commit_text(self, meta) -> tuple[int, int]:
        """Dołącza fragmenty tekstu do indeksu (BM25 + zerowe wektory i maska False; wołać pod blokadą aplikacji)."""
        start = len(self.meta)
        n = len(meta)
        if not n:
            return start, 0
        self.meta = self.meta + meta
        zeros = np.zeros((n, 384), np.float32)
        self.vec = np.vstack([self.vec, zeros]) if len(self.vec) else zeros
        mask = np.zeros(n, dtype=bool)
        self.has_vec = np.concatenate([self.has_vec, mask]) if len(self.has_vec) else mask
        self.db.executemany("INSERT INTO docs(rowid, text) VALUES (?, ?)",
                            ((start + i, x["text"].lower()) for i, x in enumerate(meta)))
        return start, n

    def fill_vectors(self, start: int, v, gen: int) -> bool:
        """Wpisuje partię policzonych wektorów i ustawia maskę has_vec; ignoruje nieaktualne pokolenie indeksu."""
        if gen != self.gen or not len(v):
            return False
        end = start + len(v)
        if start < 0 or end > len(self.vec):
            return False
        self.vec[start:end] = v
        self.has_vec[start:end] = True
        return True

    def remove_file(self, p) -> int:
        """Usuwa wszystkie fragmenty pliku z indeksu (np. po anulowaniu). Wołać pod blokadą aplikacji."""
        target = str(Path(p))
        keep = [i for i, m in enumerate(self.meta) if m["file"] != target]
        removed = len(self.meta) - len(keep)
        if not removed:
            return 0
        self.meta = [self.meta[i] for i in keep]
        self.vec = self.vec[keep] if keep else np.zeros((0, 384), np.float32)
        self.has_vec = self.has_vec[keep] if keep else np.zeros(0, dtype=bool)
        if self.only_files:
            self.only_files.discard(target)
        self.db.execute("DROP TABLE IF EXISTS docs")
        self.db.execute("CREATE VIRTUAL TABLE docs USING fts5(text, tokenize='unicode61')")
        if self.meta:
            self.db.executemany("INSERT INTO docs(rowid, text) VALUES (?, ?)",
                                ((i, m["text"].lower()) for i, m in enumerate(self.meta)))
        self.gen += 1
        return removed

    def commit_file(self, m, v) -> int:
        """Dołącza policzone fragmenty do indeksu (szybkie; wołać pod blokadą aplikacji)."""
        start = len(self.meta)
        self.meta = self.meta + m
        if len(v):
            self.vec = np.vstack([self.vec, v]) if len(self.vec) else v
            mask = np.ones(len(v), dtype=bool)
            self.has_vec = np.concatenate([self.has_vec, mask]) if len(self.has_vec) else mask
        self.db.executemany("INSERT INTO docs(rowid, text) VALUES (?, ?)",
                            ((start + i, x["text"].lower()) for i, x in enumerate(m)))
        return len(m)

    def documents(self):
        """Lista plików w indeksie: ścieżka względna, liczba fragmentów."""
        cnt = {}
        for m in self.meta:
            cnt[m["file"]] = cnt.get(m["file"], 0) + 1
        out = []
        for f, n in sorted(cnt.items()):
            try:
                rel = str(Path(f).relative_to(self.folder))
            except ValueError:
                rel = Path(f).name
            out.append({"id": rel.replace("\\", "/"), "name": Path(f).stem, "chunks": n})
        return out

    def file_by_id(self, doc_id: str):
        for f in {m["file"] for m in self.meta}:
            try:
                rel = str(Path(f).relative_to(self.folder)).replace("\\", "/")
            except ValueError:
                rel = Path(f).name
            if rel == doc_id:
                return Path(f)
        return None

    def _lexical(self, query: str, allowed=None):
        terms = [t for t in _WORD.findall(query.lower()) if len(t) >= 3]
        if not terms:
            return []
        expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        lim = self.depth if allowed is None else 100000
        rows = [r[0] for r in self.db.execute("SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs) LIMIT ?", (expr, lim))]
        if allowed is not None:
            rows = [r for r in rows if r in allowed]
        return rows[: self.depth]

    def search(self, query: str, k: int = 5):
        if not self.meta or not query.strip():
            return []
        allowed = None
        if self.only_files:
            allowed = {i for i, m in enumerate(self.meta) if m["file"] in self.only_files}
            if not allowed:
                return []
            idx = np.array(sorted(i for i in allowed if self.has_vec[i]), dtype=np.int64)
        else:
            idx = np.flatnonzero(self.has_vec)
        if len(idx):
            q = self.emb(["query: " + query])[0]
            dense = idx[np.argsort(-(self.vec[idx] @ q))][: self.depth].tolist()
        else:
            dense = []
        fused = {}
        for r, i in enumerate(dense, 1):
            fused[i] = fused.get(i, 0.0) + 1 / (60 + r)
        for r, i in enumerate(self._lexical(query, allowed), 1):
            fused[i] = fused.get(i, 0.0) + 1 / (60 + r)
        cand = sorted(fused, key=lambda i: -fused[i])[: self.rerank_n]
        if not cand:
            return []
        scores = self.rr(query, [self.meta[i]["text"] for i in cand])
        ranked = sorted(zip(cand, scores), key=lambda x: -x[1])
        if not self.passages:
            out = []
            for i, s in ranked[:k]:
                m = self.meta[i]
                out.append({"file": m["file"], "start_line": m["start_line"], "snippet": m["text"],
                            "locator": f"lines {m['start_line']}-{m['end_line']}", "score": fused[i], "rerank_score": float(s)})
            return out
        # Tryb fragmentów: w najlepszych kandydatach oceniamy krótkie okna (ustęp/punkt), bo szum wokół właściwego
        # zdania obniża ocenę całego fragmentu, a reranker widzi tylko ok. 256 pierwszych tokenów fragmentu.
        wins = []
        for i, s in ranked[: self.passage_top]:
            for w in windows(self.meta[i]["text"]):
                wins.append((i, s, w))
        wscores = self.rr(query, [w[2]["text"] for w in wins]) if wins else []
        best = {}
        for (i, s, w), ws in zip(wins, wscores):
            if i not in best or ws > best[i][0]:
                best[i] = (ws, w)
        items = []
        for i, s in ranked:
            ws, w = best.get(i, (None, None))
            items.append((max(s, ws) if ws is not None else s, i, w))
        items.sort(key=lambda x: -x[0])
        out = []
        for sc, i, w in items[:k]:
            m = self.meta[i]
            # do modelu trafia cały fragment (kontekst), a najlepsze okno służy tylko do oceny i podświetlenia w UI
            out.append({"file": m["file"], "start_line": m["start_line"], "snippet": m["text"],
                        "locator": f"lines {m['start_line']}-{m['end_line']}", "score": fused[i], "rerank_score": float(sc),
                        "best_window": w["text"] if w else None})
        return out


def make_retriever(index: Index):
    def retrieve(query: str, k: int):
        out = []
        for h in index.search(query, k):
            out.append(Source(n=0, text=superscripts(h["snippet"]), file=h["file"], locator=h["locator"],
                              label=legal_label(h["file"], h["start_line"], h["snippet"]),
                              score=h["score"], rerank=h["rerank_score"]))
        return out
    return retrieve
