"""Test natychmiastowego indeksowania BM25 i liczenia wektorów w tle (bez pytest)."""
from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sejf.retriever_simple import Index  # noqa: E402
from sejf.uploads import UploadQueue  # noqa: E402

MODELS_DIR = Path(r"C:\Users\ninja\AppData\Local\Programs\Linda Sejf\models")


def generate_polish_text(lines_count: int = 15000, marker: str = "zażółćkod7781") -> str:
    """Generuje duży polski dokument (~3000 fragmentów) z unikalnym słowem kluczowym w środku."""
    base_lines = [
        "Regulamin organizacyjny jednostki określa zasady obiegu dokumentów oraz odpowiedzialności służbowej pracowników.",
        "Każdy dokument wpływający do kancelarii podlega rejestracji w systemie ewidencji najpóźniej następnego dnia roboczego.",
        "Kierownik działu weryfikuje kompletność załączników i przekazuje sprawę do właściwego referatu merytorycznego.",
        "W przypadku stwierdzenia braków formalnych pracownik przygotowuje wezwanie do uzupełnienia w terminie siedmiu dni.",
        "Archiwizacja akt prowadzona jest zgodnie z jednolitym rzeczowym wykazem akt oraz przepisami o ochronie danych.",
    ]
    mid = lines_count // 2
    out = []
    for i in range(lines_count):
        if i == mid:
            out.append(
                f"Paragraf specjalny {i}: identyfikator procedury awaryjnej to {marker} i obowiązuje przy rozliczeniu delegacji."
            )
        else:
            out.append(f"Punkt {i + 1}: {base_lines[i % len(base_lines)]}")
    return "\n".join(out) + "\n"


def wait_for_state(q: UploadQueue, job_id: int, states: tuple[str, ...], timeout: float = 240.0) -> dict:
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        for j in q.list():
            if j["id"] == job_id and j["state"] in states:
                return j
        time.sleep(0.02)
    raise TimeoutError(f"Zadanie {job_id} nie osiągnęło stanu {states} w {timeout} s: {q.list()}")


def main():
    assert MODELS_DIR.is_dir(), f"Brak katalogu modeli: {MODELS_DIR}"
    t_total = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="sejf_instant_") as tmp:
        tmp_path = Path(tmp)

        # ---- Test (a) i (b): duży plik (~3000 fragmentów), natychmiastowy BM25 + wektory w tle ----
        docs_ab = tmp_path / "docs_ab"
        state_ab = tmp_path / "state_ab"
        docs_ab.mkdir()
        lock = threading.Lock()
        idx = Index(docs_ab, MODELS_DIR, state_ab, threads=4, passages=True)
        q = UploadQueue(lambda: idx, lock, log=lambda *a: None)

        big_file = docs_ab / "duzy_regulamin.txt"
        big_file.write_text(generate_polish_text(12000, "zażółćkod7781"), encoding="utf-8")

        t0 = time.perf_counter()
        job = q.submit(big_file, big_file.name)
        j_search = wait_for_state(q, job["id"], ("searchable", "done"), timeout=10.0)
        t_searchable = time.perf_counter() - t0
        print(f"[a] submit -> searchable: {t_searchable:.3f} s (stan={j_search['state']}, fragmenty={j_search['chunks']})")
        assert t_searchable < 5.0, f"Za wolne przejście do searchable: {t_searchable:.2f} s"
        assert j_search["chunks"] >= 2800, f"Oczekiwano ~3000 fragmentów, jest {j_search['chunks']}"

        with lock:
            hits_bm25 = idx.search("zażółćkod7781", k=5)
        assert hits_bm25 and hits_bm25[0]["file"] == str(big_file), f"Brak wyniku BM25 w stanie searchable: {hits_bm25}"
        print(f"[a] search('zażółćkod7781') w searchable OK (trafień: {len(hits_bm25)}, rerank={hits_bm25[0]['rerank_score']:.3f})")

        j_done = wait_for_state(q, job["id"], ("done", "error"), timeout=240.0)
        t_done = time.perf_counter() - t0
        print(f"[b] submit -> done (wszystkie wektory): {t_done:.2f} s (stan={j_done['state']}, done={j_done['done']}/{j_done['total']})")
        assert j_done["state"] == "done" and not j_done["error"], f"Błąd zadania: {j_done}"
        assert len(idx.has_vec) == len(idx.meta) == j_done["chunks"]
        assert bool(idx.has_vec.all()), "Nie wszystkie wiersze mają has_vec=True po zakończeniu"

        cache_file = idx._cache_path(big_file)
        assert cache_file.exists(), f"Brak pliku cache npz: {cache_file}"

        with lock:
            hits_after_vec = idx.search("zażółćkod7781", k=5)
            hits_semantic = idx.search("zasady obiegu dokumentów w kancelarii", k=5)
            idx._build()
            hits_rebuilt = idx.search("zażółćkod7781", k=5)
            hits_rebuilt_sem = idx.search("zasady obiegu dokumentów w kancelarii", k=5)

        assert [(h["file"], h["start_line"], h["snippet"]) for h in hits_after_vec] == [
            (h["file"], h["start_line"], h["snippet"]) for h in hits_rebuilt
        ], "Wynik search('zażółćkod7781') różni się po _build"
        assert [(h["file"], h["start_line"], h["snippet"]) for h in hits_semantic] == [
            (h["file"], h["start_line"], h["snippet"]) for h in hits_rebuilt_sem
        ], "Wynik search znaczeniowego różni się po _build"
        print("[b] Maska cała True, cache npz istnieje, wyniki search identyczne z _build")

        # ---- Test (c): anulowanie w stanie searchable usuwa plik i jego fragmenty ----
        cancel_file = docs_ab / "do_anulowania.txt"
        cancel_file.write_text(generate_polish_text(4000, "anulowanykod9912"), encoding="utf-8")
        t_c0 = time.perf_counter()
        jc = q.submit(cancel_file, cancel_file.name)
        wait_for_state(q, jc["id"], ("searchable",), timeout=10.0)
        with lock:
            assert idx.search("anulowanykod9912", k=3), "Plik powinien być przeszukiwalny przed anulowaniem"
        assert q.cancel(jc["id"]), "cancel() w stanie searchable powinno zwrócić True"
        jc_end = wait_for_state(q, jc["id"], ("cancelled",), timeout=30.0)
        t_cancel = time.perf_counter() - t_c0
        print(f"[c] Anulowanie w searchable: {t_cancel:.2f} s (stan={jc_end['state']})")
        assert not cancel_file.exists(), "Anulowany plik powinien zostać usunięty z dysku"
        with lock:
            assert not any(m["file"] == str(cancel_file) for m in idx.meta), "Fragmenty anulowanego pliku zostały w meta"
            assert len(idx.meta) == len(idx.vec) == len(idx.has_vec)
            hits_after_cancel = idx.search("anulowanykod9912", k=10)
            assert all(
                h["file"] != str(cancel_file) and "anulowanykod9912" not in h["snippet"]
                for h in hits_after_cancel
            ), f"Anulowany plik wciąż pojawia się w wynikach search: {hits_after_cancel}"

        # ---- Test (d): przebudowa w trakcie liczenia wektorów nie psuje indeksu (gen) ----
        docs_d = tmp_path / "docs_d"
        state_d = tmp_path / "state_d"
        docs_d.mkdir()
        d_file = docs_d / "przebudowa.txt"
        d_file.write_text(generate_polish_text(4000, "przebudowakod5521"), encoding="utf-8")

        # Zostawiamy folder pusty na starcie, żeby wgrać plik przez kolejkę i wywołać reload w trakcie liczenia wektorów
        d_empty = tmp_path / "docs_d_empty"
        d_empty.mkdir()
        idx_d = Index(d_empty, MODELS_DIR, state_d, threads=4, passages=True)
        q_d = UploadQueue(lambda: idx_d, lock, log=lambda *a: None)
        jd = q_d.submit(d_file, d_file.name)
        wait_for_state(q_d, jd["id"], ("searchable",), timeout=10.0)
        time.sleep(0.2)
        with lock:
            old_gen = idx_d.gen
            idx_d.reload(docs_d)
            new_gen = idx_d.gen
            assert new_gen > old_gen
            ignored = idx_d.fill_vectors(0, np.ones((5, 384), np.float32), old_gen)
            assert ignored is False, "fill_vectors ze starym gen powinno zostać zignorowane"
            assert not idx_d.has_vec[:5].any(), "Stare fill_vectors nadpisało maskę po przebudowie"
        jd_end = wait_for_state(q_d, jd["id"], ("done", "error", "cancelled"), timeout=60.0)
        with lock:
            assert idx_d.gen == new_gen
            assert len(idx_d.meta) == len(idx_d.vec) == len(idx_d.has_vec)
            hits_d = idx_d.search("przebudowakod5521", k=3)
            assert hits_d and hits_d[0]["file"] == str(d_file)
        print(f"[d] Przebudowa w trakcie liczenia wektorów OK (gen {old_gen} -> {new_gen}, stan zadania={jd_end['state']})")

        # ---- Test (e): _build z nowym plikiem bez cache wraca szybko (< 5 s dla ~3000 fragmentów) ----
        docs_e = tmp_path / "docs_e"
        state_e = tmp_path / "state_e"
        docs_e.mkdir()
        e_file = docs_e / "start_bez_cache.txt"
        e_file.write_text(generate_polish_text(12000, "startkod3394"), encoding="utf-8")

        t_e0 = time.perf_counter()
        idx_e = Index(docs_e, MODELS_DIR, state_e, threads=4, passages=True)
        t_build = time.perf_counter() - t_e0
        print(f"[e] _build (3000 fragmentów bez cache): {t_build:.3f} s (fragmenty={len(idx_e.meta)}, pending={len(idx_e.pending_vectors)})")
        assert t_build < 5.0, f"_build bez cache zbyt wolny: {t_build:.2f} s"
        assert len(idx_e.meta) >= 2800
        assert not idx_e.has_vec.any(), "Plik bez cache powinien mieć has_vec=False po _build"
        assert idx_e.pending_vectors == [e_file]
        hits_e = idx_e.search("startkod3394", k=5)
        assert hits_e and hits_e[0]["file"] == str(e_file), f"Plik z _build nie jest przeszukiwalny po słowach: {hits_e}"

        # Dodatkowe sprawdzenie: submit_vectors nie usuwa pliku przy cancel oraz błąd e5 w searchable zachowuje plik/BM25
        q_e = UploadQueue(lambda: idx_e, lock, log=lambda *a: None)
        je = q_e.submit_vectors(e_file, e_file.name)
        wait_for_state(q_e, je["id"], ("searchable",), timeout=10.0)
        q_e.cancel(je["id"])
        je_end = wait_for_state(q_e, je["id"], ("cancelled", "done"), timeout=30.0)
        assert e_file.exists(), "Anulowanie submit_vectors NIE może usuwać pliku użytkownika"
        assert idx_e.search("startkod3394", k=5), "Anulowanie submit_vectors nie może usuwać pliku z indeksu"
        print(f"[e+] submit_vectors cancel zachował plik i BM25 (stan={je_end['state']})")

        err_file = docs_e / "blad_e5.txt"
        err_file.write_text(generate_polish_text(50, "blednykod4410"), encoding="utf-8")
        orig_emb = idx_e.emb
        idx_e.emb = lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("symulowany błąd ONNX"))
        j_err = q_e.submit(err_file, err_file.name)
        j_err_end = wait_for_state(q_e, j_err["id"], ("done", "error"), timeout=10.0)
        idx_e.emb = orig_emb
        assert j_err_end["state"] == "done" and j_err_end["error"].startswith("wektory niepoliczone:"), j_err_end
        assert err_file.exists(), "Błąd e5 w stanie searchable nie może usuwać pliku"
        assert idx_e.search("blednykod4410", k=3)[0]["file"] == str(err_file)
        print(f"[e+] Błąd e5 w searchable -> done z ostrzeżeniem, BM25 działa ({j_err_end['error']})")

    print(f"WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE w {time.perf_counter() - t_total:.2f} s")


if __name__ == "__main__":
    main()
