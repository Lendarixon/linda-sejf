"""Porównanie wyszukiwarki open source z wynikami Linda Probe (te same pytania, ten sam reranker).

Wejście: plik pytań z zapisanymi źródłami Linda Probe (q_b.json: question, kind, act, arts, sources[].rerank, retr_hit_at5).
Wyjście: zgodność decyzji bramki (max rerank >= 0,9), trafienie właściwego artykułu w top 5, czas.
Użycie: python tools/validate_retriever.py <q_b.json> <models_dir> [out.json]
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sejf.labels import superscripts  # noqa: E402
from sejf.retriever_simple import Index, make_retriever  # noqa: E402

Q = json.load(open(sys.argv[1], encoding="utf-8"))
models = sys.argv[2]
out_p = sys.argv[3] if len(sys.argv) > 3 else "validate_b.json"
ROOT = Path(__file__).resolve().parents[1]
t = time.time()
idx = Index(ROOT / "corpus", models, ROOT / "state", threads=8)
print("indeks", len(idx.meta), "fragmentów", round(time.time() - t, 1), "s", flush=True)
retrieve = make_retriever(idx)


def act_of(label):
    m = re.search(r"Dz\.U\. (\d{4}) poz\. (\d+)", label or "")
    return f"DU_{m.group(1)}_{m.group(2)}" if m else None


def arts_of(label):
    m = re.search(r", art\. ([\w¹²³⁴⁵⁶⁷⁸⁹⁰, ]+)$", label or "")
    return {a.strip() for a in m.group(1).split(",")} if m else set()


def gold_arts(it):
    a = it.get("arts") or [it.get("art")]
    if isinstance(a, str):
        a = json.loads(a.replace("'", '"')) if a.startswith("[") else [a]
    return {superscripts(x) for x in a if x}


rows, t = [], time.time()
for i, it in enumerate(Q):
    src = retrieve(it["question"], 5)
    new_max = max((s.rerank for s in src), default=0.0)
    old_max = max((s["rerank"] for s in it["sources"]), default=0.0)
    r = {"q": it["question"], "kind": it["kind"], "old_max": old_max, "new_max": new_max,
         "old_pass": old_max >= 0.9, "new_pass": new_max >= 0.9}
    if it["kind"] == "in":
        r["old_hit5"] = bool(it.get("retr_hit_at5"))
        r["new_hit5"] = any(act_of(s.label) == it["act"] and bool(gold_arts(it) & arts_of(s.label)) for s in src)
    rows.append(r)
    if i % 25 == 0:
        print(i, len(Q), round(time.time() - t), "s", flush=True)
n = len(rows)
I = [r for r in rows if r["kind"] == "in"]
T = [r for r in rows if r["kind"] != "in"]
rep = {
    "n": n, "s_per_q": round((time.time() - t) / n, 2),
    "gate_agree": round(sum(r["old_pass"] == r["new_pass"] for r in rows) / n, 3),
    "pass_old": round(sum(r["old_pass"] for r in I) / len(I), 3), "pass_new": round(sum(r["new_pass"] for r in I) / len(I), 3),
    "traps_refused_old": f'{sum(not r["old_pass"] for r in T)}/{len(T)}', "traps_refused_new": f'{sum(not r["new_pass"] for r in T)}/{len(T)}',
    "hit5_old": round(sum(r["old_hit5"] for r in I) / len(I), 3), "hit5_new": round(sum(r["new_hit5"] for r in I) / len(I), 3),
    "hit5_among_pass_new": round(sum(r["new_hit5"] for r in I if r["new_pass"]) / max(1, sum(r["new_pass"] for r in I)), 3),
    "hit5_among_pass_old": round(sum(r["old_hit5"] for r in I if r["old_pass"]) / max(1, sum(r["old_pass"] for r in I)), 3),
}
print(json.dumps(rep, ensure_ascii=False, indent=1))
json.dump({"report": rep, "rows": rows}, open(out_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
