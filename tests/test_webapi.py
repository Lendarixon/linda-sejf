from sejf.retriever_simple import windows
from sejf.webapi import safe_upload_name


def test_upload_name_blocks_paths_and_types():
    assert safe_upload_name("regulamin.pdf") == "regulamin.pdf"
    assert safe_upload_name("../../Windows/evil.txt") == "evil.txt"
    assert safe_upload_name("C:\\x\\umowa.docx") == "umowa.docx"
    assert safe_upload_name("skrypt.exe") is None
    assert safe_upload_name(".hidden.txt") is None
    assert safe_upload_name("") is None


def test_windows_cover_all_lines():
    text = "\n".join(f"wiersz {i} " + "x" * 120 for i in range(12))
    w = windows(text)
    covered = set()
    for x in w:
        covered |= set(x["text"].split("\n"))
    assert covered == set(text.split("\n"))
    assert all(len(x["text"]) <= 380 + 130 for x in w)


def test_upload_name_windows_rules():
    assert safe_upload_name("CON.txt") is None
    assert safe_upload_name("a<b.pdf") is None
    assert safe_upload_name("x.docx.") == "x.docx"
    assert safe_upload_name("Umowa ąę.txt") == "Umowa ąę.txt"
    assert safe_upload_name(r"..\..\x.pdf") == "x.pdf"
