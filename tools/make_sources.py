"""Źródła z wyszukiwarki open source dla pliku pytań (format q_*.json z polem sources), do generacji i oceny sędziów.
Użycie: python tools/make_sources.py <q_in.json> <models_dir> <q_out.json> [k] [passages 0/1]"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sejf.retriever_simple import Index, make_retriever  # noqa: E402

src, models, dst = sys.argv[1], sys.argv[2], sys.argv[3]
k = int(sys.argv[4]) if len(sys.argv) > 4 else 5
passages = len(sys.argv) > 5 and sys.argv[5] == "1"
ROOT = Path(__file__).resolve().parents[1]
idx = Index(ROOT / "corpus", models, ROOT / "state", threads=8, passages=passages)
retrieve = make_retriever(idx)
Q = json.load(open(src, encoding="utf-8"))
out = []
for i, it in enumerate(Q):
    s = retrieve(it["question"], k)
    it = dict(it)
    it["sources"] = [{"n": j + 1, "label": x.label, "locator": x.locator, "text": x.text, "score": x.score, "rerank": x.rerank}
                     for j, x in enumerate(s)]
    out.append(it)
    if i % 25 == 0:
        print(i, len(Q), flush=True)
json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
print("ok", dst)
