"""Kolejka dodawania plików: natychmiastowe indeksowanie tekstu (BM25) i liczenie wektorów partiami w tle.

Plik jest zapisany w folderze dokumentów od razu; po szybkim odczycie tekstu trafia do indeksu (stan „searchable”),
więc wyszukiwanie po słowach działa natychmiast, a wektory e5 liczą się partiami bez blokowania pytań.
Anulowanie pliku dodanego przez /api/upload usuwa go z dysku i indeksu; dla plików już obecnych w folderze
(`submit_vectors`) anulowanie albo błąd przerywa tylko liczenie wektorów bez kasowania pliku użytkownika.
"""
from __future__ import annotations

import itertools
import queue
import threading
import time
from pathlib import Path

import numpy as np

VEC_BATCH = 256


class Cancelled(Exception):
    pass


class UploadQueue:
    def __init__(self, get_index, lock, busy=lambda: False, log=print, keep: int = 30, vec_batch: int = VEC_BATCH):
        self.get_index, self.lock, self.busy, self.log, self.keep = get_index, lock, busy, log, keep
        self.vec_batch = vec_batch
        self.jobs: list[dict] = []
        self._ids = itertools.count(1)
        self._q: queue.Queue = queue.Queue()
        self._mx = threading.Lock()
        threading.Thread(target=self._loop, daemon=True).start()

    def _enqueue(self, path: Path, name: str, vectors_only: bool, delete_on_fail: bool) -> dict:
        job = {"id": next(self._ids), "name": name, "path": str(path), "state": "queued", "done": 0, "total": 0,
               "chunks": 0, "error": "", "started": 0.0, "finished": 0.0, "cancel": False,
               "vectors_only": vectors_only, "delete_on_fail": delete_on_fail}
        with self._mx:
            if vectors_only:
                for j in self.jobs:
                    if j["path"] == job["path"] and j["state"] == "queued":
                        return self.public(j)
            self.jobs.append(job)
            done = [j for j in self.jobs if j["state"] in ("done", "error", "cancelled")]
            for j in done[:max(0, len(self.jobs) - self.keep)]:
                self.jobs.remove(j)
        self._q.put(job)
        return self.public(job)

    def submit(self, path: Path, name: str) -> dict:
        """Dodaje nowy plik z /api/upload — w razie anulowania lub błędu odczytu plik jest usuwany."""
        return self._enqueue(path, name, vectors_only=False, delete_on_fail=True)

    def submit_vectors(self, path: Path, name: str = "") -> dict:
        """Liczy wektory w tle dla pliku już wczytanego tekstowo przy starcie/przebudowie (bez kasowania pliku)."""
        return self._enqueue(path, name or Path(path).name, vectors_only=True, delete_on_fail=False)

    @staticmethod
    def public(j: dict) -> dict:
        d = {k: j[k] for k in ("id", "name", "state", "done", "total", "chunks", "error", "started", "finished")}
        d["vec_started"] = j.get("vec_started", 0.0)
        return d

    def list(self):
        with self._mx:
            return [self.public(j) for j in self.jobs]

    def active(self) -> bool:
        with self._mx:
            return any(j["state"] in ("queued", "indexing", "searchable") for j in self.jobs)

    def cancel(self, job_id: int) -> bool:
        with self._mx:
            for j in self.jobs:
                if j["id"] == job_id and j["state"] in ("queued", "indexing", "searchable"):
                    j["cancel"] = True
                    return True
        return False

    def _loop(self):
        while True:
            job = self._q.get()
            try:
                self._run(job)
            except Exception as e:  # nie zatrzymujemy kolejki przez jeden plik
                with self._mx:
                    job.update(state="error", error=str(e)[:200], finished=time.time())

    def _run(self, job: dict):
        path = Path(job["path"])
        delete_on_fail = job["delete_on_fail"]
        vectors_only = job["vectors_only"]

        def set_job(**kw):
            with self._mx:
                job.update(**kw)

        if job["cancel"]:
            if delete_on_fail:
                path.unlink(missing_ok=True)
            set_job(state="cancelled", finished=time.time())
            return
        while self.busy():  # przebudowa całego folderu ma pierwszeństwo
            time.sleep(0.5)
        if job["cancel"]:
            if delete_on_fail:
                path.unlink(missing_ok=True)
            set_job(state="cancelled", finished=time.time())
            return
        set_job(state="indexing", started=time.time())

        try:
            if vectors_only:
                with self.lock:
                    index = self.get_index()
                    gen = index.gen
                    indices = [i for i, m in enumerate(index.meta) if m["file"] == str(path)]
                    if not indices:
                        set_job(state="done", chunks=0, done=0, total=0, finished=time.time())
                        return
                    if all(index.has_vec[i] for i in indices):
                        n = len(indices)
                        set_job(state="done", chunks=n, done=n, total=n, finished=time.time())
                        return
                    start, n = indices[0], len(indices)
                    meta = [index.meta[i] for i in indices]
            else:
                index = self.get_index()
                meta = index.prepare_text(path)
                if job["cancel"]:
                    raise Cancelled()
                with self.lock:
                    index = self.get_index()
                    gen = index.gen
                    existing = [i for i, m in enumerate(index.meta) if m["file"] == str(path)]
                    if existing:  # przebudowa w międzyczasie już go dodała
                        n = len(existing)
                        if all(index.has_vec[i] for i in existing):
                            set_job(state="done", chunks=n, done=n, total=n, finished=time.time())
                            return
                        start = existing[0]
                        meta = [index.meta[i] for i in existing]
                    else:
                        start, n = index.commit_text(meta)
        except Cancelled:
            if delete_on_fail:
                path.unlink(missing_ok=True)
            set_job(state="cancelled", finished=time.time())
            self.log("anulowano dodawanie:", job["name"])
            return
        except Exception as e:
            if delete_on_fail:
                path.unlink(missing_ok=True)
            set_job(state="error", error=str(e)[:200], finished=time.time())
            self.log("błąd dodawania:", job["name"], type(e).__name__, str(e)[:200])
            return

        if not n:
            set_job(state="done", chunks=0, done=0, total=0, finished=time.time(),
                    error="Nie udało się odczytać tekstu (skan bez OCR?).")
            self.log("dodano plik:", job["name"], 0, "fragmentów,", round(job["finished"] - job["started"], 1), "s")
            return

        set_job(state="searchable", chunks=n, done=0, total=n, vec_started=time.time())
        vecs = []
        try:
            for off in range(0, n, self.vec_batch):
                if job["cancel"]:
                    raise Cancelled()
                part_meta = meta[off:off + self.vec_batch]

                def progress(sub_done, _sub_total, base=off):
                    set_job(done=base + sub_done, total=n)
                    if job["cancel"]:
                        raise Cancelled()

                v = index.embed_meta(path, part_meta, progress=progress)
                vecs.append(v)
                with self.lock:
                    cur = self.get_index()
                    if not cur.fill_vectors(start + off, v, gen):
                        set_job(state="done", finished=time.time())
                        self.log("przerwano wektory po przebudowie:", job["name"])
                        return
                    index = cur
            if job["cancel"]:
                raise Cancelled()
            full_v = np.vstack(vecs) if len(vecs) > 1 else vecs[0]
            index.save_cache(path, meta, full_v)
        except Cancelled:
            if delete_on_fail:
                with self.lock:
                    self.get_index().remove_file(path)
                path.unlink(missing_ok=True)
                set_job(state="cancelled", chunks=0, finished=time.time())
            else:
                set_job(state="cancelled", finished=time.time())
            self.log("anulowano dodawanie:", job["name"])
            return
        except Exception as e:
            set_job(state="done", error="wektory niepoliczone: " + str(e)[:150], finished=time.time())
            self.log("błąd wektorów:", job["name"], type(e).__name__, str(e)[:200])
            return

        set_job(state="done", chunks=n, done=n, total=n, finished=time.time())
        self.log("dodano plik:", job["name"], n, "fragmentów,", round(job["finished"] - job["started"], 1), "s")
