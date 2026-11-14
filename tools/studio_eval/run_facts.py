"""Ponowny przebieg „terminy, kwoty” po zmianie polecenia (pełne zdania)."""
import json
import sys
import time
import urllib.request

URL = "http://127.0.0.1:8775"
F = "firma/{} — Przykład sp. z o.o. (dokument fikcyjny).txt"
DOCS = ["nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md",
        F.format("Zasady podróży służbowych"), F.format("Procedura ochrony danych osobowych")]
res = []
for doc in DOCS:
    t = time.time()
    r = urllib.request.Request(URL + "/api/tool", method="POST",
                               data=json.dumps({"tool": "facts", "documents": [doc], "topic": "", "options": {}}).encode(),
                               headers={"Content-Type": "application/json", "Origin": URL})
    d = json.loads(urllib.request.urlopen(r, timeout=900).read())
    d["_case"] = {"tool": "facts", "docs": [doc], "topic": "", "opts": {}, "wall_s": round(time.time() - t, 1)}
    res.append(d)
    ok = sum(1 for s in d["sentences"] if s["status"] == "supported")
    print(doc[:40], d["status"], f"{ok}/{len(d['sentences'])}", d["_case"]["wall_s"], "s", flush=True)
    for s in d["sentences"]:
        print("  ", s["status"][:5], s["text"], flush=True)
json.dump(res, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
