import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sejf.core import Source
from sejf import cite

SRC = [Source(0, "Art. 154. § 1. Wymiar urlopu wynosi:\n1) 20 dni – jeżeli pracownik jest zatrudniony krócej niż 10 lat;\n2) 26 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat.\n§ 2. Wymiar urlopu dla pracownika w niepełnym wymiarze ustala się proporcjonalnie.", label="KP, art. 154"),
       Source(0, "Art. 152. § 1. Pracownikowi przysługuje prawo do corocznego urlopu.\n§ 2. Pracownik nie może zrzec się prawa do urlopu.", label="KP, art. 152")]

def _ret(q, k):
    return [Source(**vars(s)) for s in SRC]

def test_units_split_by_editorial_units():
    for i, s in enumerate(SRC, 1):
        s.n = i
    us = cite.units(SRC)
    texts = [u.text for u in us]
    assert any(t.startswith("2) 26 dni") for t in texts), texts
    assert any(t.startswith("§ 2. Pracownik nie może") for t in texts), texts

def test_quotes_are_verbatim_and_conclusion_verified():
    def gen(msgs):
        body = msgs[1]["content"]
        sid = [l.split("]")[0][1:] for l in body.splitlines() if "26 dni" in l][0]
        return '{"fragmenty": ["%s", "S999"], "wniosek": "Po 12 latach przysługuje 26 dni urlopu."}' % sid
    a, sources, us = cite.ask("Ile urlopu po 12 latach?", _ret, gen, verifier=lambda p: [0.9] * len(p), threshold=0.5)
    assert a.status == "answered" and len(a.quotes) == 1          # nieistniejący S999 odrzucony
    assert a.quotes[0].text in " ".join(s.text.replace("\n", " ") for s in sources)
    assert a.conclusion_ok is True

def test_empty_selection_is_refusal():
    a, _, _ = cite.ask("Kurs euro?", _ret, lambda m: '{"fragmenty": [], "wniosek": ""}')
    assert a.status == "refused"

def test_non_json_fallback():
    a, _, us = cite.ask("x", _ret, lambda m: "Właściwy fragment to S2.")
    assert a.status == "answered" and a.quotes[0].sid == "S2"
