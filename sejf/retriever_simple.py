"""Samodzielna wyszukiwarka Sejfu (wersja open source, bez Linda Probe).

Hybryda: znaczeniowa (multilingual-e5-small, ONNX) + słowna (SQLite FTS5, BM25), łączone RRF,
potem polski reranker (sdadas/polish-reranker-base-ranknet, ONNX, sigmoid) ocenia 30 najlepszych.
Ocena rerankera trafia do bramki odmowy Sejfu (min_rerank_score, domyślnie 0,9).

Indeks jest zapisywany w <state>/index_<hash>.npz/.json i odbudowywany, gdy pliki się zmienią.
Obsługiwane pliki: .txt, .md (UTF-8); .pdf i .docx, jeśli zainstalowano pypdf / python-docx.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path

import numpy as np

from .core import Source
from .labels import legal_label, superscripts

TEXT_EXT = {".txt", ".md"}
_MIN_CHUNK = 150


# ------------------------------------------------------------------ pliki i fragmenty
def read_text(p: Path) -> str:
    s = p.suffix.lower()
    if s in TEXT_EXT:
        return p.read_text(encoding="utf-8", errors="replace")
    if s == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            return ""
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    if s == ".docx":
        try:
            import docx
        except ImportError:
            return ""
        return "\n".join(par.text for par in docx.Document(str(p)).paragraphs)
    return ""


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

    def __call__(self, texts, batch: int = 32):
        out = []
        for i in range(0, len(texts), batch):
            h, mask = self.m.run(texts[i:i + batch])
            mask = mask[..., None].astype(np.float32)
            v = (h * mask).sum(1) / np.clip(mask.sum(1), 1e-9, None)
            out.append(v / np.linalg.norm(v, axis=1, keepdims=True))
        return np.vstack(out) if out else np.zeros((0, 384), np.float32)


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
                 passages: bool = False, passage_top: int = 15):
        self.passages, self.passage_top = passages, passage_top
        self.only_files = None  # zbiór pełnych ścieżek plików, do których zawęża się wyszukiwanie (wybór źródeł w UI)
        self.folder = Path(folder)
        self.models = Path(models_dir)
        self.state = Path(state_dir)
        self.state.mkdir(parents=True, exist_ok=True)
        self.rerank_n, self.depth = rerank_n, depth
        self.emb = Embedder(self.models / "e5", threads)
        self.rr = Reranker(self.models / "reranker", threads)
        self._build()

    def _files(self):
        exts = TEXT_EXT | {".pdf", ".docx"}
        return sorted(p for p in self.folder.rglob("*") if p.is_file() and p.suffix.lower() in exts)

    def _file_part(self, p: Path):
        """Fragmenty i wektory jednego pliku; pamięć podręczna per plik (ścieżka + rozmiar + data zmiany)."""
        st = p.stat()
        key = hashlib.sha256(f"{p}|{st.st_size}|{st.st_mtime_ns}".encode()).hexdigest()[:20]
        cache = self.state / "files" / f"{key}.npz"
        if cache.exists():
            z = np.load(cache, allow_pickle=False)
            return json.loads(str(z["meta"])), z["v"]
        meta = []
        for c in chunks(read_text(p)):
            c["file"] = str(p)
            meta.append(c)
        vec = self.emb(["passage: " + p.stem + "\n" + m["text"] for m in meta]).astype(np.float32) if meta \
            else np.zeros((0, 384), np.float32)
        cache.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache, v=vec, meta=np.array(json.dumps(meta, ensure_ascii=False)))
        return meta, vec

    def _build(self):
        self.meta, vecs = [], []
        for p in self._files():
            m, v = self._file_part(p)
            self.meta += m
            vecs.append(v)
        self.vec = np.vstack(vecs) if vecs else np.zeros((0, 384), np.float32)
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute("CREATE VIRTUAL TABLE docs USING fts5(text, tokenize='unicode61')")
        self.db.executemany("INSERT INTO docs(rowid, text) VALUES (?, ?)",
                            ((i, m["text"].lower()) for i, m in enumerate(self.meta)))

    def add_file(self, p) -> int:
        """Dodaje nowy plik do działającego indeksu (bez przebudowy całości). Zwraca liczbę fragmentów."""
        p = Path(p)
        m, v = self._file_part(p)
        start = len(self.meta)
        self.meta += m
        self.vec = np.vstack([self.vec, v]) if len(v) else self.vec
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
        q = self.emb(["query: " + query])[0]
        allowed = None
        if self.only_files:
            allowed = {i for i, m in enumerate(self.meta) if m["file"] in self.only_files}
            if not allowed:
                return []
            idx = np.fromiter(allowed, dtype=np.int64)
            dense = idx[np.argsort(-(self.vec[idx] @ q))][: self.depth].tolist()
        else:
            dense = np.argsort(-(self.vec @ q))[: self.depth].tolist()
        fused = {}
        for r, i in enumerate(dense, 1):
            fused[i] = fused.get(i, 0.0) + 1 / (60 + r)
        for r, i in enumerate(self._lexical(query, allowed), 1):
            fused[i] = fused.get(i, 0.0) + 1 / (60 + r)
        cand = sorted(fused, key=lambda i: -fused[i])[: self.rerank_n]
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
