"""Przebieg jakości studia 1.4 na działającej aplikacji (GPU): każde narzędzie i opcja, zapis do results.json."""
import json
import sys
import time
import urllib.request

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8775"
OUT = sys.argv[2] if len(sys.argv) > 2 else "results.json"
F = "firma/{} — Przykład sp. z o.o. (dokument fikcyjny).txt"
EKO = "nauka/Notatki z wykładu — Podstawy ekonomii, popyt i podaż (materiał przykładowy).md"
REG, DEL, RODO = F.format("Regulamin pracy"), F.format("Zasady podróży służbowych"), F.format("Procedura ochrony danych osobowych")
KP = "Kodeks pracy (Dz.U. 2026 poz. 1245).txt"
LONG = sys.argv[3] if len(sys.argv) > 3 else ""

CASES = [
    ("summary", [EKO], "", {"length": "short", "form": "prose"}),
    ("summary", [EKO], "", {"length": "long", "form": "points"}),
    ("summary", [REG], "", {"length": "standard", "form": "prose"}),
    ("quiz", [EKO], "", {"length": "standard"}),
    ("quiz", [DEL], "", {"length": "short"}),
    ("glossary", [EKO], "", {}),
    ("glossary", [RODO], "", {}),
    ("simple", [RODO], "", {"length": "standard"}),
    ("simple", [KP], "urlop wypoczynkowy", {"length": "short"}),
    ("claims", [EKO], "", {}),
    ("facts", [EKO], "", {}),
    ("memo", [EKO], "elastyczność cenowa popytu", {}),
    ("memo", [EKO], "przepis na pierogi", {}),
]
if LONG:
    CASES.append(("summary", [LONG], "", {"length": "short", "form": "prose"}))


def post(path, body):
    r = urllib.request.Request(URL + path, data=json.dumps(body).encode(), method="POST",
                               headers={"Content-Type": "application/json", "Origin": URL})
    try:
        return json.loads(urllib.request.urlopen(r, timeout=1800).read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")


res = []
for tool, docs, topic, opts in CASES:
    t = time.time()
    d = post("/api/tool", {"tool": tool, "documents": docs, "topic": topic, "options": opts})
    d["_case"] = {"tool": tool, "docs": docs, "topic": topic, "opts": opts, "wall_s": round(time.time() - t, 1)}
    res.append(d)
    sents = d.get("sentences", [])
    ok = sum(1 for s in sents if s.get("status") == "supported")
    print(f"{tool:9} {str(opts):42} {topic[:22]:22} {d.get('status', d.get('error', '?'))[:40]:12} "
          f"{ok}/{len(sents)} {d['_case']['wall_s']} s parts={d.get('parts')}", flush=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("DONE", flush=True)
