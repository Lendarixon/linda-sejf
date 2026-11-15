"""Kolejka dodawania plików: liczenie wektorów w tle, bez blokowania pytań, z postępem i anulowaniem.

Plik jest zapisany w folderze dokumentów od razu; jego fragmenty i wektory liczy osobny wątek (bez blokady aplikacji),
a do indeksu dołącza je szybki krok pod blokadą. Anulowanie albo błąd usuwa plik, więc folder i indeks zostają zgodne.
"""
from __future__ import annotations

import itertools
import queue
import threading
import time
from pathlib import Path


class Cancelled(Exception):
    pass


class UploadQueue:
    def __init__(self, get_index, lock, busy=lambda: False, log=print, keep: int = 30):
        self.get_index, self.lock, self.busy, self.log, self.keep = get_index, lock, busy, log, keep
        self.jobs: list[dict] = []
        self._ids = itertools.count(1)
        self._q: queue.Queue = queue.Queue()
        self._mx = threading.Lock()
        threading.Thread(target=self._loop, daemon=True).start()

    def submit(self, path: Path, name: str) -> dict:
        job = {"id": next(self._ids), "name": name, "path": str(path), "state": "queued", "done": 0, "total": 0,
               "chunks": 0, "error": "", "started": 0.0, "finished": 0.0, "cancel": False}
        with self._mx:
            self.jobs.append(job)
            done = [j for j in self.jobs if j["state"] in ("done", "error", "cancelled")]
            for j in done[:max(0, len(self.jobs) - self.keep)]:
                self.jobs.remove(j)
        self._q.put(job)
        return self.public(job)

    @staticmethod
    def public(j: dict) -> dict:
        return {k: j[k] for k in ("id", "name", "state", "done", "total", "chunks", "error", "started", "finished")}

    def list(self):
        with self._mx:
            return [self.public(j) for j in self.jobs]

    def active(self) -> bool:
        with self._mx:
            return any(j["state"] in ("queued", "indexing") for j in self.jobs)

    def cancel(self, job_id: int) -> bool:
        with self._mx:
            for j in self.jobs:
                if j["id"] == job_id and j["state"] in ("queued", "indexing"):
                    j["cancel"] = True
                    return True
        return False

    def _loop(self):
        while True:
            job = self._q.get()
            try:
                self._run(job)
            except Exception as e:  # nie zatrzymujemy kolejki przez jeden plik
                job.update(state="error", error=str(e)[:200], finished=time.time())

    def _run(self, job: dict):
        path = Path(job["path"])
        if job["cancel"]:
            path.unlink(missing_ok=True)
            job.update(state="cancelled", finished=time.time())
            return
        while self.busy():  # przebudowa całego folderu ma pierwszeństwo
            time.sleep(0.5)
        job.update(state="indexing", started=time.time())

        def progress(done, total):
            job.update(done=done, total=total)
            if job["cancel"]:
                raise Cancelled()
        index = self.get_index()
        try:
            m, v = index.prepare_file(path, progress=progress)
            with self.lock:
                index = self.get_index()
                if any(x["file"] == str(path) for x in index.meta):  # przebudowa w międzyczasie już go dodała
                    n = sum(1 for x in index.meta if x["file"] == str(path))
                else:
                    n = index.commit_file(m, v)
        except Cancelled:
            path.unlink(missing_ok=True)
            job.update(state="cancelled", finished=time.time())
            self.log("anulowano dodawanie:", job["name"])
            return
        except Exception as e:
            path.unlink(missing_ok=True)
            job.update(state="error", error=str(e)[:200], finished=time.time())
            self.log("błąd dodawania:", job["name"], type(e).__name__, str(e)[:200])
            return
        job.update(state="done", chunks=n, done=job["total"] or n, total=job["total"] or n, finished=time.time())
        if not n:
            job["error"] = "Nie udało się odczytać tekstu (skan bez OCR?)."
        self.log("dodano plik:", job["name"], n, "fragmentów,", round(job["finished"] - job["started"], 1), "s")
