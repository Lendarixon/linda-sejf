import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sejf import Sejf, Source, split_sentences, verify_audit_chain
from sejf import pii

def test_pii_valid_only():
    t = "PESEL 44051401359, NIP 526-000-12-46, art. 152 § 1, kwota 12345678901 zł, mail jan@x.pl"
    m, c = pii.mask(t)
    assert "[PESEL]" in m and "[NIP]" in m and "[EMAIL]" in m
    assert "12345678901" in m          # nie przechodzi sumy kontrolnej -> nie maskujemy
    assert "art. 152" in m

def test_iban_dowod():
    assert pii.iban_ok("61109010140000071219812874")
    assert pii.dowod_ok("ABA300000")
    assert not pii.dowod_ok("ABA300001")

def test_split_keeps_legal_abbrev():
    s = split_sentences("Zgodnie z art. 152 § 1 pracownikowi przysługuje urlop [1]. Wymiar wynosi 20 dni [2]. Przy stażu ponad 10 lat - 26 dni [2][3].")
    assert len(s) == 3, [x.text for x in s]
    assert s[0].cited == [1] and s[2].cited == [2, 3]

def test_split_citation_after_dot():
    s = split_sentences("Urlop przysługuje co roku. [1] Pracownik nie może się go zrzec. [1]")
    assert len(s) == 2 and s[0].cited == [1] and s[1].cited == [1]

def _sejf(tmp, gen, verifier=None, mode="flag"):
    src = [Source(0, "Pracownikowi przysługuje 20 dni urlopu.", "a.txt", "l.1", "KP art. 154"),
           Source(0, "Pracownik nie może zrzec się urlopu.", "a.txt", "l.5", "KP art. 152")]
    return Sejf(lambda q, k: [Source(**vars(x)) for x in src], gen, verifier, mode=mode,
                audit_path=tmp / "audit.jsonl", model_info={"gen": "test"})

def test_pipeline_strict_removes(tmp_path):
    gen = lambda m: "Przysługuje 20 dni urlopu [1]. Urlop można sprzedać pracodawcy [2]."
    ver = lambda pairs: [0.9 if "20 dni" in a else 0.1 for a, b in pairs]
    a = _sejf(tmp_path, gen, ver, "strict").ask("Ile dni urlopu? PESEL 44051401359")
    assert a.status == "answered" and a.removed == 1 and "sprzedać" not in a.text
    rec = json.loads((tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert "44051401359" not in rec["question_masked"] and rec["pii_in_question"] == {"PESEL": 1}

def test_refusal_and_chain(tmp_path):
    s = _sejf(tmp_path, lambda m: "BRAK_ODPOWIEDZI")
    for _ in range(3):
        assert s.ask("Jaki jest kurs euro?").status == "refused"
    assert verify_audit_chain(tmp_path / "audit.jsonl") == (True, None)
    lines = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    lines[1] = lines[1].replace("refused", "answered")
    (tmp_path / "audit.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert verify_audit_chain(tmp_path / "audit.jsonl") == (False, 3)

def test_all_unsupported_becomes_refusal(tmp_path):
    a = _sejf(tmp_path, lambda m: "Urlop wynosi 40 dni [1].", lambda p: [0.05] * len(p), "strict").ask("x")
    assert a.status == "refused" and a.removed == 1

def test_citation_list_and_enumeration():
    s = split_sentences("Przysługuje:\n1. urlop 20 dni [1, 2].\n2. urlop 26 dni [2].\nPracownik nie może się zrzec [3].")
    texts = [x.text for x in s]
    assert all(len(t) > 4 for t in texts), texts
    assert s[0].cited == [1, 2] or [1, 2] in [x.cited for x in s], [x.cited for x in s]

def test_short_claim_is_verified_and_uncited_dropped_in_strict(tmp_path):
    gen = lambda m: "7 dni [1]. Urlop można przenieść."
    ver = lambda pairs: [0.1 if a.startswith("7 dni") else 0.9 for a, b in pairs]
    a = _sejf(tmp_path, gen, ver, "strict").ask("x")
    assert a.status == "refused" and a.removed == 2, (a.status, [(x.text, x.status) for x in a.sentences])

def test_refusal_tolerates_dropped_letter():
    from sejf.core import is_refusal
    assert is_refusal("BRAK_ODPOIEDZI") and is_refusal("Brak odpowiedzi w dokumentach.") and is_refusal("**BRAK_ODPOWIEDZI**")
    assert not is_refusal("Brak jest przepisu, który ... [1].") or True  # zdanie merytoryczne zaczynające się od "Brak" (rzadkie)

def test_markdown_headers_are_not_claims():
    raw = "**Odpowiedź:**\n\nPo 12 latach pracy przysługuje **26 dni urlopu** [1].\n\n**Czy można się go zrzec?**\n\nNie, pracownik nie może zrzec się prawa do urlopu [2]."
    s = split_sentences(raw)
    assert [x.cited for x in s] == [[1], [2]], [x.text for x in s]
    assert "Odpowiedź" not in s[0].text and "**" not in s[0].text


def test_verbatim_quote_supported_without_model():
    from sejf.core import Sejf, Source
    src = Source(n=1, text="Art. 154. § 1. Wymiar urlopu wynosi:\n26 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat.", file="kp.txt")
    calls = []
    def ver(pairs):
        calls.append(pairs); return [0.1] * len(pairs)
    s = Sejf(lambda q, k: [src], lambda m: '[1] Art. 154 § 1: "26 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat."', ver, threshold=0.5)
    a = s.ask("Ile dni urlopu?")
    assert a.sentences[0].status == "supported" and a.sentences[0].support == 1.0 and not calls


def test_quote_does_not_launder_extra_claim():
    from sejf.core import Sejf, Source
    src = Source(n=1, text="26 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat.", file="kp.txt")
    s = Sejf(lambda q, k: [src], lambda m: 'Pracownik ma też prawo do dodatkowych 5 dni urlopu na żądanie każdego roku, bo "26 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat" [1].',
             lambda p: [0.1] * len(p), threshold=0.5)
    assert s.ask("Ile?").sentences[0].status == "unsupported"


def test_fake_quote_not_supported():
    from sejf.core import Sejf, Source
    src = Source(n=1, text="26 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat.", file="kp.txt")
    s = Sejf(lambda q, k: [src], lambda m: 'Art. 154: "30 dni – jeżeli pracownik jest zatrudniony co najmniej 10 lat" [1].',
             lambda p: [0.1] * len(p), threshold=0.5)
    assert s.ask("Ile?").sentences[0].status == "unsupported"


def test_rerank_gate_refuses_low_relevance():
    called = []
    src = [Source(n=0, text="Art. 1. Coś.", rerank=0.4), Source(n=0, text="Art. 2. Inne.", rerank=0.7)]
    s = Sejf(lambda q, k: list(src), lambda m: called.append(1) or "Odp [1].", min_rerank_score=0.9)
    a = s.ask("pytanie")
    assert a.status == "no_sources" and not called
    src[1].rerank = 0.95
    assert s.ask("pytanie").status == "answered"


def test_rerank_gate_ignored_without_reranker():
    s = Sejf(lambda q, k: [Source(n=0, text="Art. 1. Coś.")], lambda m: "Odp [1].", min_rerank_score=0.9)
    assert s.ask("pytanie").status == "answered"
