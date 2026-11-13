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
    def __init__(self, folder, models_dir, state_dir, threads: int = 4, rerank_n: int = 30, depth: int = 60):
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

    def _build(self):
        files = self._files()
        sig = hashlib.sha256("\n".join(f"{p}|{p.stat().st_size}|{p.stat().st_mtime_ns}" for p in files).encode()).hexdigest()[:16]
        meta_p, vec_p = self.state / f"index_{sig}.json", self.state / f"index_{sig}.npz"
        if meta_p.exists() and vec_p.exists():
            self.meta = json.loads(meta_p.read_text(encoding="utf-8"))
            self.vec = np.load(vec_p)["v"]
        else:
            self.meta = []
            for p in files:
                for c in chunks(read_text(p)):
                    c["file"] = str(p)
                    self.meta.append(c)
            self.vec = self.emb(["passage: " + Path(m["file"]).stem + "\n" + m["text"] for m in self.meta]).astype(np.float32)
            np.savez_compressed(vec_p, v=self.vec)
            meta_p.write_text(json.dumps(self.meta, ensure_ascii=False), encoding="utf-8")
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute("CREATE VIRTUAL TABLE docs USING fts5(text, tokenize='unicode61')")
        self.db.executemany("INSERT INTO docs(rowid, text) VALUES (?, ?)",
                            ((i, m["text"].lower()) for i, m in enumerate(self.meta)))

    def _lexical(self, query: str):
        terms = [t for t in _WORD.findall(query.lower()) if len(t) >= 3]
        if not terms:
            return []
        expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
        rows = self.db.execute("SELECT rowid FROM docs WHERE docs MATCH ? ORDER BY bm25(docs) LIMIT ?", (expr, self.depth)).fetchall()
        return [r[0] for r in rows]

    def search(self, query: str, k: int = 5):
        if not self.meta or not query.strip():
            return []
        q = self.emb(["query: " + query])[0]
        dense = np.argsort(-(self.vec @ q))[: self.depth].tolist()
        fused = {}
        for r, i in enumerate(dense, 1):
            fused[i] = fused.get(i, 0.0) + 1 / (60 + r)
        for r, i in enumerate(self._lexical(query), 1):
            fused[i] = fused.get(i, 0.0) + 1 / (60 + r)
        cand = sorted(fused, key=lambda i: -fused[i])[: self.rerank_n]
        scores = self.rr(query, [self.meta[i]["text"] for i in cand])
        order = sorted(zip(cand, scores), key=lambda x: -x[1])[:k]
        out = []
        for i, s in order:
            m = self.meta[i]
            out.append({"file": m["file"], "start_line": m["start_line"], "snippet": m["text"],
                        "locator": f"lines {m['start_line']}-{m['end_line']}", "score": fused[i], "rerank_score": float(s)})
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
