from pathlib import Path

import pytest

from sejf import tools


class FakeIndex:
    def __init__(self, n_chunks):
        self.meta = [{"file": str(Path("C:/d/regulamin.txt")), "start_line": i * 10 + 1, "end_line": i * 10 + 9,
                      "text": f"§ {i}. Pracownik ma {i} dni."} for i in range(n_chunks)]
        self.only_files = None
        self.searched = None

    def file_by_id(self, doc_id):
        return Path("C:/d/regulamin.txt") if doc_id == "regulamin.txt" else None

    def search(self, query, k):
        self.searched = (query, set(self.only_files or []))
        return [{"file": m["file"], "start_line": m["start_line"], "snippet": m["text"], "locator": "x",
                 "rerank_score": 0.9} for m in self.meta[:k]]


def test_short_document_goes_in_whole_and_in_order():
    src, scope = tools.gather_sources(FakeIndex(5), ["regulamin.txt"])
    assert scope == "cały dokument"
    assert [s.n for s in src] == [1, 2, 3, 4, 5]
    assert src[0].text.startswith("§ 0.")


def test_long_document_needs_topic():
    with pytest.raises(ValueError):
        tools.gather_sources(FakeIndex(tools.MAX_FULL_CHUNKS + 1), ["regulamin.txt"])


def test_long_document_with_topic_uses_search_in_selected_files():
    idx = FakeIndex(tools.MAX_FULL_CHUNKS + 5)
    src, scope = tools.gather_sources(idx, ["regulamin.txt"], "urlop")
    assert idx.searched == ("urlop", {str(Path("C:/d/regulamin.txt"))})
    assert len(src) == tools.TOPIC_K and "urlop" in scope
    assert idx.only_files is None  # zawężenie przywrócone po wyszukiwaniu


def test_intro_filter():
    assert tools._INTRO.match("Poniżej przedstawiam notatkę")
    assert tools._INTRO.match("**Notatka służbowa: urlop**")
    assert not tools._INTRO.match("Otoczenie biura jest monitorowane")


def test_memo_prompt_contains_topic():
    src, _ = tools.gather_sources(FakeIndex(2), ["regulamin.txt"])
    msgs = tools.build_messages("memo", src, "praca zdalna")
    assert "praca zdalna" in msgs[1]["content"] and "[1]" in msgs[1]["content"]
