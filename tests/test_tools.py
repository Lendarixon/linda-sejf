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


def test_very_long_document_needs_topic():
    with pytest.raises(ValueError):
        tools.gather_sources(FakeIndex(tools.MAX_FULL_CHUNKS * tools.MAX_PARTS + 1), ["regulamin.txt"])


def test_long_document_split_into_equal_parts_with_global_numbers():
    parts, scope = tools.gather_parts(FakeIndex(tools.MAX_FULL_CHUNKS + 6), ["regulamin.txt"])
    assert len(parts) == 2 and "2 częściach" in scope
    assert [s.n for s in parts[1]][0] == len(parts[0]) + 1
    assert abs(len(parts[0]) - len(parts[1])) <= 1


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


class FakeSejf:
    def __init__(self):
        self.audited = []

    def _verify(self, sents, sources):
        for x in sents:
            x.status = "supported" if "dni" in x.text else "unsupported"

    def _audit(self, ans, user):
        self.audited.append(ans)


def test_parse_lines_keeps_cited_items_and_drops_headers():
    raw = "**Słowniczek pojęć:**\n- Urlop — przerwa w pracy [1]\n- Delegacja: wyjazd służbowy [2]\nOto lista:"
    items = tools.parse_lines(raw)
    assert [i.cited for i in items] == [[1], [2]]
    assert items[0].text.startswith("Urlop")


def test_quiz_question_mark_does_not_split_and_answer_is_verified_with_question():
    raw = "- P: Ile dni urlopu ma pracownik? | O: 20 dni [1]\n- P: Kto zatwierdza? | O: przełożony [1]\nŚmieci bez formatu [1]"
    sj = FakeSejf()
    d = tools.run_tool(sj, FakeIndex(3), lambda m: raw, "quiz", ["regulamin.txt"])
    assert d["status"] == "answered" and d["kind"] == "qa"
    assert len(d["sentences"]) == 2  # wiersz bez formatu P/O odrzucony
    assert [s["status"] for s in d["sentences"]] == ["supported", "unsupported"]


def test_options_change_prompt():
    src, _ = tools.gather_sources(FakeIndex(2), ["regulamin.txt"])
    short = tools.build_messages("summary", src, "", {"length": "short"})[1]["content"]
    points = tools.build_messages("summary", src, "", {"form": "points"})[1]["content"]
    assert "3–4 zdaniach" in short and "punktach" in points and "- " in points


def test_parts_each_generated_and_prefixed():
    calls = []

    def gen(m):
        calls.append(m)
        return "Tekst mówi o dniach pracy [1]."
    d = tools.run_tool(FakeSejf(), None or FakeIndex(tools.MAX_FULL_CHUNKS + 6), gen, "summary", ["regulamin.txt"])
    assert len(calls) == 2 and d["parts"] == 2
    assert not d["sentences"][0]["text"].startswith("Część")
    assert "czego dotyczy tekst" not in calls[0][1]["content"]  # przy częściach bez zdania-wstępu w każdej


def test_quiz_count_is_capped_to_chosen_option():
    raw = "\n".join(f"- P: Pytanie {i} o dni? | O: {i} dni [1]" for i in range(12))
    d = tools.run_tool(FakeSejf(), FakeIndex(3), lambda m: raw, "quiz", ["regulamin.txt"], opts={"length": "short"})
    assert len(d["sentences"]) == 5


def test_unknown_option_values_fall_back():
    src, _ = tools.gather_sources(FakeIndex(2), ["regulamin.txt"])
    msg = tools.build_messages("summary", src, "", {"length": "<script>"})[1]["content"]
    assert "5–8" in msg


class OnlyTwoSejf(FakeSejf):
    """Potwierdza zdanie tylko fragmentem [2]."""

    def _verify(self, sents, sources):
        for x in sents:
            ok = 2 in x.cited and any(s.n == 2 for s in sources)
            x.status, x.best_source, x.support = ("supported", 2, 0.99) if ok else ("unsupported", None, 0.1)


def test_wrong_neighbour_citation_is_renumbered_and_flagged():
    d = tools.run_tool(OnlyTwoSejf(), FakeIndex(3), lambda m: "- Pojęcie — wyjaśnienie z tekstu [1]",
                       "glossary", ["regulamin.txt"])
    s = d["sentences"][0]
    assert s["cited"] == [2] and s["status"] == "supported" and s.get("renumbered")
