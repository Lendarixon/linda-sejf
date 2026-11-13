import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sejf.labels import legal_label, _file_lines, _doc_title

def _f(tmp_path):
    lines = ["Art. 151. § 1. Praca w godzinach nadliczbowych.", "§ 2. Coś dalej o nadgodzinach w zakładzie pracy i dalej.",
             "Urlopy wypoczynkowe", "Art. 152. § 1. Pracownikowi przysługuje urlop.", "§ 2. Nie może się zrzec.",
             "Art. 153. § 1. Pierwszy urlop.", "§ 2. Kolejne urlopy w następnych latach kalendarzowych pracownik nabywa."]
    p = tmp_path / "Kodeks pracy (Dz.U. 2026 poz. 1245).txt"
    p.write_text("\n".join(lines), encoding="utf-8")
    _file_lines.cache_clear(); _doc_title.cache_clear()
    return str(p), lines

def test_heading_start(tmp_path):
    p, L = _f(tmp_path)
    assert legal_label(p, 3, "\n".join(L[2:5])) == "Kodeks pracy (Dz.U. 2026 poz. 1245), art. 152"

def test_mid_article_start(tmp_path):
    p, L = _f(tmp_path)
    assert legal_label(p, 5, "\n".join(L[4:7])).endswith("art. 152, 153") or legal_label(p, 5, "\n".join(L[4:7])).endswith("art. 153")

def test_body_prefix(tmp_path):
    p, L = _f(tmp_path)
    assert legal_label(p, 7, L[6]).endswith("art. 153")

def test_superscript_articles(tmp_path):
    from sejf.labels import superscripts
    lines = ["Art. 22. § 1. Przez nawiązanie stosunku pracy.", "Art. 22[1]. § 1. Pracodawca żąda danych osobowych.", "§ 1[1]. Coś dalej."]
    p = tmp_path / "Kodeks pracy (Dz.U. 2026 poz. 1245).txt"
    p.write_text("\n".join(lines), encoding="utf-8")
    _file_lines.cache_clear(); _doc_title.cache_clear()
    assert legal_label(str(p), 2, "\n".join(lines[1:])).endswith("art. 22¹")
    assert superscripts("§ 1[1]. art. 22[1] i [1]") == "§ 1¹. art. 22¹ i [1]"
