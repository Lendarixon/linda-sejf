import threading
import time
from pathlib import Path

import numpy as np
import pytest

from sejf.store import Store
from sejf.uploads import UploadQueue


def test_store_roundtrip_list_and_delete(tmp_path):
    st = Store(tmp_path)
    a = st.save("rozmowy", {"title": "Urlop", "data": {"items": [1, 2]}, "count": 2})
    b = st.save("rozmowy", {"title": "Delegacja", "data": {}})
    assert [x["title"] for x in st.list("rozmowy")] == ["Delegacja", "Urlop"]
    assert st.get("rozmowy", a["id"])["data"] == {"items": [1, 2]}
    st.save("rozmowy", {"id": a["id"], "title": "Urlop 2", "data": {}})
    assert st.get("rozmowy", a["id"])["title"] == "Urlop 2" and len(st.list("rozmowy")) == 2
    assert st.delete("rozmowy", b["id"]) and not st.delete("rozmowy", b["id"])


@pytest.mark.parametrize("bad", ["../x", "a/../../b", "ABCDEF", "x", "a" * 41, "abc def"])
def test_store_rejects_unsafe_ids(tmp_path, bad):
    with pytest.raises(ValueError):
        Store(tmp_path).get("rozmowy", bad)


def test_store_rejects_unknown_collection_and_huge_items(tmp_path):
    st = Store(tmp_path)
    with pytest.raises(ValueError):
        st.list("../etc")
    with pytest.raises(ValueError):
        st.save("studio", {"title": "x", "data": "a" * 4_100_000})


class FakeIndex:
    def __init__(self, n=50, slow=0.0):
        self.meta, self.n, self.slow = [], n, slow

    def prepare_file(self, p, progress=None):
        for i in range(0, self.n, 10):
            time.sleep(self.slow)
            if progress:
                progress(min(i + 10, self.n), self.n)
        return [{"file": str(p), "text": f"t{i}"} for i in range(self.n)], np.zeros((self.n, 384), np.float32)

    def commit_file(self, m, v):
        self.meta += m
        return len(m)


def wait(q, state, timeout=5):
    t = time.time()
    while time.time() - t < timeout:
        if all(j["state"] == state for j in q.list()):
            return True
        time.sleep(0.02)
    return False


def test_upload_queue_indexes_in_background_and_reports_progress(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x")
    idx = FakeIndex(50)
    q = UploadQueue(lambda: idx, threading.Lock(), log=lambda *a: None)
    q.submit(p, "a.txt")
    assert wait(q, "done")
    j = q.list()[0]
    assert j["chunks"] == 50 and j["done"] == j["total"] == 50 and len(idx.meta) == 50


def test_upload_queue_cancel_removes_file_and_does_not_touch_index(tmp_path):
    p = tmp_path / "big.txt"
    p.write_text("x")
    idx = FakeIndex(400, slow=0.05)
    q = UploadQueue(lambda: idx, threading.Lock(), log=lambda *a: None)
    j = q.submit(p, "big.txt")
    time.sleep(0.15)
    assert q.cancel(j["id"])
    assert wait(q, "cancelled")
    assert not p.exists() and idx.meta == []


def test_upload_queue_does_not_hold_lock_while_embedding(tmp_path):
    """Pytania (blokada aplikacji) muszą działać w trakcie liczenia wektorów dużego pliku."""
    p = tmp_path / "big.txt"
    p.write_text("x")
    lock = threading.Lock()
    q = UploadQueue(lambda: FakeIndex(300, slow=0.05), lock, log=lambda *a: None)
    q.submit(p, "big.txt")
    time.sleep(0.2)
    assert q.list()[0]["state"] == "indexing"
    assert lock.acquire(timeout=0.2)
    lock.release()


def test_upload_queue_skips_duplicate_when_reindex_already_added_it(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x")
    idx = FakeIndex(5)
    idx.meta = [{"file": str(p), "text": "już jest"}]
    q = UploadQueue(lambda: idx, threading.Lock(), log=lambda *a: None)
    q.submit(p, "a.txt")
    assert wait(q, "done")
    assert len(idx.meta) == 1 and q.list()[0]["chunks"] == 1
