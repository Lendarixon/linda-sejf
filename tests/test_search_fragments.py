from pathlib import Path

from sejf import webapi


class FakeIndex:
    folder = Path("C:/d")

    def __init__(self):
        f = str(Path("C:/d/firma/regulamin.txt"))
        self.meta = [
            {"file": f, "start_line": 1, "end_line": 5, "text": "Urlop na żądanie: do 4 dni w roku, zgłoszenie przed 9:00."},
            {"file": f, "start_line": 6, "end_line": 9, "text": "Młodociany ma urlop 26 dni roboczych, art. 205."},
            {"file": f, "start_line": 10, "end_line": 12, "text": "Delegacja BR105 rozliczana w 14 dni."},
        ]
        self.only_files = None
        self.searched = []

    def search(self, q, k):
        self.searched.append(q)
        return [{"file": m["file"], "start_line": m["start_line"], "snippet": m["text"], "rerank_score": 0.9 - i / 10}
                for i, m in enumerate(self.meta)]


def test_parse_query_syntax():
    text, phrases, excludes, codes = webapi.parse_query('urlop „na żądanie” -młodociany art. 205')
    assert phrases == ["na żądanie"] and excludes == ["młodociany"] and "205" in codes
    assert "urlop" in text and "na żądanie" in text and "młodociany" not in text


def test_exact_phrase_filters_fragments():
    d = webapi.search_fragments(FakeIndex(), '"na żądanie"')
    assert d["exact"] and [h["line"] for h in d["hits"]] == [1]
    assert d["hits"][0]["id"] == "firma/regulamin.txt"


def test_code_must_match_whole_token():
    d = webapi.search_fragments(FakeIndex(), "BR105")
    assert [h["line"] for h in d["hits"]] == [10]
    d = webapi.search_fragments(FakeIndex(), "BR10")
    assert d["hits"] == []


def test_exclusion_removes_semantic_hits():
    d = webapi.search_fragments(FakeIndex(), "urlop -młodociany")
    assert 6 not in [h["line"] for h in d["hits"]] and 1 in [h["line"] for h in d["hits"]]


def test_scope_is_respected_for_exact_scan():
    idx = FakeIndex()
    idx.only_files = {"C:/inny.txt"}
    assert webapi.search_fragments(idx, '"na żądanie"')["hits"] == []


def test_empty_query():
    assert webapi.search_fragments(FakeIndex(), "  ")["hits"] == []
