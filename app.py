"""Linda Sejf — lokalna aplikacja. Serwer HTTP na 127.0.0.1; okno programu (launcher.py) albo przeglądarka.

Przepływ: wyszukiwarka (e5 + BM25 + polski reranker, ONNX) -> bramka odmowy (słaba ocena rerankera = odmowa bez modelu)
-> model językowy w llama.cpp (domyślnie Gemma-4-E4B Q6_K) -> weryfikator zdań (HerBERT, ONNX int8) -> dziennik audytu.
Nic nie jest wysyłane do internetu; połączenia tylko do lokalnego llama-server.

Ustawienia: %LOCALAPPDATA%/LindaSejf/config.json (zmieniane z okna „Ustawienia”) albo zmienne środowiskowe
SEJF_DOCS, SEJF_MODELS, SEJF_GGUF, SEJF_LLAMA, SEJF_PORT, SEJF_MIN_RERANK, SEJF_THREADS, SEJF_PASSAGES.
Uruchomienie bez okna: python app.py (otwiera przeglądarkę; SEJF_NO_BROWSER=1 — nie otwiera).
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sejf import Sejf, tools, verifier_onnx, webapi  # noqa: E402
from sejf.core import verify_audit_chain  # noqa: E402
from sejf.retriever_simple import Index, make_retriever  # noqa: E402
from sejf.store import Store  # noqa: E402
from sejf.uploads import UploadQueue  # noqa: E402

VERSION = "1.5.2"
DATA = Path(os.environ.get("SEJF_DATA", Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LindaSejf"))
DATA.mkdir(parents=True, exist_ok=True)
CFG_P = DATA / "config.json"
MODES = {"normal": 0.7, "careful": 0.95}


def load_cfg():
    try:
        return json.loads(CFG_P.read_text(encoding="utf-8-sig")) if CFG_P.exists() else {}
    except (OSError, ValueError):
        return {}


def save_cfg(c):
    tmp = CFG_P.with_suffix(".tmp")
    tmp.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(CFG_P)


cfg = load_cfg()


def opt(key, env, default):
    if os.environ.get(env) not in (None, ""):
        return os.environ[env]
    return cfg[key] if cfg.get(key) is not None else default


MODELS = Path(opt("models", "SEJF_MODELS", HERE / "models"))
GGUF = Path(opt("gguf", "SEJF_GGUF", MODELS / "gemma-4-E4B-it-Q6_K.gguf"))
LLAMA = Path(opt("llama", "SEJF_LLAMA", HERE / "bin" / ("llama-server.exe" if os.name == "nt" else "llama-server")))
PORT = int(opt("port", "SEJF_PORT", 8765))
LLAMA_PORT = PORT + 1
PASSAGES = int(opt("passages", "SEJF_PASSAGES", 1))
AUDIT = DATA / "sejf_audit.jsonl"


def pl(n, one, few, many):
    """Polska odmiana: 1 dokument, 2–4 dokumenty, 5+ dokumentów (12–14 też „many”)."""
    w = one if n == 1 else few if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else many
    return f"{n} {w}"


def log(*a):
    line = time.strftime("%H:%M:%S") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(DATA / "sejf.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


class State:
    """Stan aplikacji: indeks, model, ustawienia i postęp długich operacji (indeksowanie)."""

    def __init__(self):
        self.docs = Path(opt("documents", "SEJF_DOCS", HERE / "corpus"))
        self.threads = int(opt("threads", "SEJF_THREADS", max(2, (os.cpu_count() or 4) // 2)))
        env_thr = os.environ.get("SEJF_MIN_RERANK")
        self.mode = cfg.get("mode") if cfg.get("mode") in MODES else "normal"
        self.min_rerank = float(env_thr) if env_thr else float(cfg.get("min_rerank") or MODES[self.mode])
        self.job = {"busy": False, "text": "", "done": 0, "total": 0}
        self.lock = threading.Lock()   # jedna generacja / jedna przebudowa indeksu naraz
        self.index = self.sejf = self.llama = None
        self.store = Store(DATA)
        self.uploads = None
        self.vcfg = {}
        self.gpu = cfg.get("gpu") if cfg.get("gpu") in ("auto", "cpu") else "auto"
        self.device = "procesor"

    def progress(self, k, n, name):
        self.job.update(done=k, total=n, text=f"Indeksuję {k}/{n}: {name}")


S = State()


def missing_files():
    return [str(p) for p in (GGUF, LLAMA, MODELS / "e5" / "model.onnx", MODELS / "reranker" / "model.onnx",
                             MODELS / "verifier" / "model_int8.onnx") if not p.exists()]


def generate(messages, max_tokens=350):
    body = json.dumps({"messages": messages, "temperature": 0, "max_tokens": max_tokens, "cache_prompt": True,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def generate_long(messages):
    """Streszczenia, zestawienia i notatki: dłuższa odpowiedź niż w pytaniach."""
    return generate(messages, max_tokens=1100)


def gpu_devices():
    """Karty graficzne widoczne dla llama.cpp (Vulkan: AMD, NVIDIA, Intel, także zintegrowane)."""
    try:
        out = subprocess.run([str(LLAMA), "--list-devices"], capture_output=True, text=True, timeout=60,
                             creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    except Exception:
        return []
    devs = []
    for line in (out.stdout + out.stderr).splitlines():
        line = line.strip()
        if line.split(":")[0].startswith(("Vulkan", "CUDA", "ROCm", "Metal")) and ":" in line:
            dev, name = line.split(":", 1)
            devs.append((dev.strip(), name.strip().split(" (")[0]))
    return devs


def start(status=log):
    """Ładuje indeks, model i weryfikator, uruchamia serwer HTTP w wątku. Zwraca adres URL."""
    miss = missing_files()
    if miss:
        raise RuntimeError("Brak plików: " + ", ".join(miss))
    if not S.docs.is_dir():
        S.docs = HERE / "corpus"
    status(f"Wczytuję dokumenty z folderu {S.docs}…")
    t = time.time()
    S.index = Index(S.docs, MODELS, DATA / "state", threads=S.threads, passages=bool(PASSAGES),
                    progress=lambda k, n, name: status(f"Indeksuję dokumenty {k}/{n}: {name}"))
    log("indeks gotowy:", len(S.index.meta), "fragmentów,", round(time.time() - t, 1), "s")
    status("Uruchamiam model językowy…")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    accel = ["-ngl", "0"]
    if S.gpu == "auto":
        devs = gpu_devices()
        if devs:  # cały model na pierwszą kartę (zwykle osobną), bez dzielenia z kartą zintegrowaną
            accel = ["-ngl", "999", "--device", devs[0][0]]
            S.device = f"karta graficzna: {devs[0][1]}"
    log("akceleracja:", S.device)
    S.llama = subprocess.Popen([str(LLAMA), "-m", str(GGUF), "--host", "127.0.0.1", "--port", str(LLAMA_PORT), "-c", "12288",
                                "-t", str(S.threads), "-tb", str(S.threads), "--temp", "0", "-np", "1", "--jinja", "--no-webui",
                                *accel],
                               stdout=open(DATA / "llama.log", "ab"), stderr=subprocess.STDOUT, creationflags=flags)
    for _ in range(600):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{LLAMA_PORT}/health", timeout=2)
            break
        except Exception:
            if S.llama.poll() is not None:
                raise RuntimeError(f"Model nie wystartował — szczegóły w {DATA / 'llama.log'}")
            time.sleep(1)
    else:
        stop()
        raise RuntimeError(f"Model nie odpowiada po 10 minutach — szczegóły w {DATA / 'llama.log'}")
    status("Wczytuję weryfikator zdań…")
    vfn, vthr, S.vcfg = verifier_onnx.load(MODELS / "verifier", threads=S.threads)
    S.uploads = UploadQueue(lambda: S.index, S.lock, busy=lambda: S.job["busy"], log=log)
    for p in S.index.pending_vectors:
        S.uploads.submit_vectors(p, p.name)
    S.sejf = Sejf(make_retriever(S.index), generate, vfn, threshold=vthr, mode="flag", k=5,
                  min_rerank_score=S.min_rerank or None, audit_path=AUDIT,
                  model_info={"generator": GGUF.name, "verifier": S.vcfg.get("name")})
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    log("gotowe:", f"http://127.0.0.1:{PORT}/")
    return f"http://127.0.0.1:{PORT}/"


def stop():
    if S.llama and S.llama.poll() is None:
        S.llama.terminate()


def reindex(folder=None):
    """Przebudowa indeksu w tle (zmiana folderu albo odświeżenie). Folder zapisujemy w ustawieniach po sukcesie."""
    S.job.update(busy=True, done=0, total=0, text="Sprawdzam pliki…")

    def run():
        pending = []
        with S.lock:
            try:
                pending = S.index.reload(folder, progress=S.progress) or []
                if folder is not None:
                    S.docs = Path(folder)
                    c = load_cfg()
                    c["documents"] = str(S.docs)
                    save_cfg(c)
                log("indeks przebudowany:", S.docs, len(S.index.meta), "fragmentów")
                S.job.update(text="Gotowe: " + pl(len(S.index.documents()), "dokument", "dokumenty", "dokumentów"))
            except Exception as e:
                log("błąd indeksowania", type(e).__name__, str(e)[:300])
                S.job.update(text="Błąd indeksowania: " + str(e)[:200])
            finally:
                S.job["busy"] = False
        if S.uploads:
            for p in pending:
                S.uploads.submit_vectors(p, p.name)
    threading.Thread(target=run, daemon=True).start()


def settings_dict():
    return {"documents": str(S.docs), "mode": S.mode, "min_rerank": S.min_rerank, "threads": S.threads,
            "cpu": os.cpu_count(), "gpu": S.gpu, "device": S.device, "model": GGUF.name, "verifier": S.vcfg.get("name"), "data": str(DATA),
            "version": VERSION, "job": S.job}


def audit_view(limit=50):
    if not AUDIT.exists():
        return {"entries": [], "ok": True, "count": 0}
    ok, bad = verify_audit_chain(AUDIT)
    lines = AUDIT.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:][::-1]:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        out.append({"ts": r.get("ts"), "question": r.get("question_masked"), "status": r.get("status"),
                    "sources": len(r.get("sources") or []), "pii": bool(r.get("pii_in_question")),
                    "unsupported": sum(1 for s in r.get("sentences") or [] if s.get("status") == "unsupported")})
    return {"entries": out, "ok": ok, "bad_line": bad, "count": len(lines), "path": str(AUDIT)}


class H(BaseHTTPRequestHandler):
    server_version = "LindaSejf/" + VERSION
    INDEX_HTML = None

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                                                    "script-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        pass

    def _host_ok(self):
        # ochrona przed DNS rebinding: serwer odpowiada tylko na swój adres lokalny
        return self.headers.get("Host", "") in (f"127.0.0.1:{PORT}", f"localhost:{PORT}")

    def _json(self, limit=16384):
        n = int(self.headers.get("Content-Length", "0") or 0)
        if n <= 0 or n > limit:
            return {}
        return json.loads(self.rfile.read(n))

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"error": "host"})
        if self.path in ("/", "/index.html"):
            if H.INDEX_HTML is None:
                H.INDEX_HTML = (HERE / "ui" / "index.html").read_bytes()
            return self._send(200, H.INDEX_HTML, "text/html; charset=utf-8")
        if self.path == "/api/health":
            return self._send(200, {"ok": True, "model": GGUF.name, "verifier": S.vcfg.get("name"), "documents": str(S.docs),
                                    "chunks": len(S.index.meta), "min_rerank": S.min_rerank, "local": True, "upload": True,
                                    "settings": True, "store": True, "search": True, "version": VERSION})
        if self.path == "/api/docs":
            return self._send(200, webapi.docs_list(S.index))
        if self.path.startswith("/api/doc?"):
            d = webapi.doc_text(S.index, self.path)
            return self._send(200, d) if d else self._send(404, {"error": "not-found"})
        if self.path == "/api/settings":
            return self._send(200, settings_dict())
        if self.path == "/api/audit":
            return self._send(200, audit_view())
        if self.path == "/api/uploads":
            return self._send(200, {"jobs": S.uploads.list() if S.uploads else []})
        if self.path.startswith("/api/store?"):
            q = parse_qs(urlparse(self.path).query)
            c, item = (q.get("c") or [""])[0], (q.get("id") or [""])[0]
            try:
                if item:
                    d = S.store.get(c, item)
                    return self._send(200, d) if d else self._send(404, {"error": "not-found"})
                return self._send(200, {"items": S.store.list(c)})
            except ValueError as e:
                return self._send(400, {"error": str(e)})
        return self._send(404, {"error": "not-found"})

    def do_POST(self):
        if not self._host_ok() or self.headers.get("Origin") not in (None, f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self._send(403, {"error": "origin"})
        try:
            if self.path == "/api/upload":
                return self._upload()
            if self.path == "/api/ask":
                return self._ask()
            if self.path == "/api/settings":
                return self._settings()
            if self.path == "/api/tool":
                return self._tool()
            if self.path == "/api/export":
                return self._export()
            if self.path == "/api/search":
                return self._search()
            if self.path == "/api/uploads/cancel":
                body = self._json()
                return self._send(200, {"ok": bool(S.uploads and S.uploads.cancel(int(body.get("id", 0))))})
            if self.path in ("/api/store", "/api/store/delete"):
                body = self._json(limit=4_500_000)
                try:
                    if self.path == "/api/store":
                        return self._send(200, S.store.save(str(body.get("c", "")), body))
                    return self._send(200, {"ok": S.store.delete(str(body.get("c", "")), str(body.get("id", "")))})
                except ValueError as e:
                    return self._send(400, {"error": str(e)})
            if self.path == "/api/reindex":
                if S.job["busy"]:
                    return self._send(409, {"error": "Indeksowanie już trwa."})
                reindex()
                return self._send(200, {"ok": True})
        except Exception as e:
            log("błąd", self.path, type(e).__name__, str(e)[:300])
            return self._send(500, {"error": "Błąd aplikacji, zobacz sejf.log."})
        return self._send(404, {"error": "not-found"})

    def _ask(self):
        body = self._json()
        q = str(body.get("question", "")).strip()
        mode = "strict" if body.get("mode") == "strict" else "flag"
        scope = body.get("documents") or None
        if not q or len(q) > 1000:
            return self._send(400, {"error": "Pytanie musi mieć od 1 do 1000 znaków."})
        if S.job["busy"]:
            return self._send(409, {"error": "Trwa indeksowanie dokumentów — spróbuj za chwilę."})
        with S.lock:
            t0 = time.time()
            webapi.set_scope(S.index, scope if isinstance(scope, list) else None)
            S.sejf.min_rerank_score = S.min_rerank or None
            a = S.sejf.ask(q, user="local", mode=mode)
            dt = time.time() - t0
        d = a.to_dict()
        d["seconds"] = round(dt, 1)
        log("pytanie:", a.status, round(dt, 1), "s")
        return self._send(200, d)

    def _search(self):
        body = self._json()
        q = str(body.get("q", "")).strip()
        scope = body.get("documents") or None
        if not q or len(q) > 300:
            return self._send(400, {"error": "Wpisz od 1 do 300 znaków."})
        with S.lock:
            t0 = time.time()
            webapi.set_scope(S.index, scope if isinstance(scope, list) else None)
            try:
                d = webapi.search_fragments(S.index, q)
            finally:
                webapi.set_scope(S.index, None)
        d["seconds"] = round(time.time() - t0, 2)
        return self._send(200, d)

    def _tool(self):
        body = self._json()
        tool = str(body.get("tool", ""))
        topic = str(body.get("topic", "")).strip()[:300]
        docs = body.get("documents") or None
        if S.job["busy"]:
            return self._send(409, {"error": "Trwa indeksowanie dokumentów — spróbuj za chwilę."})
        with S.lock:
            t0 = time.time()
            try:
                opts = body.get("options") if isinstance(body.get("options"), dict) else {}
                d = tools.run_tool(S.sejf, S.index, generate_long, tool, docs if isinstance(docs, list) else None, topic,
                                   opts=opts)
            except ValueError as e:
                return self._send(400, {"error": str(e)})
        d["seconds"] = round(time.time() - t0, 1)
        log("narzędzie:", tool, d["status"], d["seconds"], "s")
        return self._send(200, d)

    def _export(self):
        body = self._json(limit=2_000_000)
        md = str(body.get("markdown", ""))
        if not md.strip():
            return self._send(400, {"error": "Notatnik jest pusty."})
        out = DATA / "notatki"
        out.mkdir(parents=True, exist_ok=True)
        # fiszki: plik CSV (pytanie;odpowiedź) do importu w Anki albo Quizlet; nazwa pliku ustalana tutaj, nie przez stronę
        csv = body.get("format") == "csv"
        p = out / time.strftime("fiszki-%Y%m%d-%H%M%S.csv" if csv else "notatnik-%Y%m%d-%H%M%S.md")
        p.write_text(md, encoding="utf-8")
        log("zapisano:", p)
        return self._send(200, {"ok": True, "path": str(p)})

    def _settings(self):
        body = self._json()
        c = load_cfg()
        msg = []
        if body.get("mode") in MODES:
            S.mode, S.min_rerank = body["mode"], MODES[body["mode"]]
            c["mode"] = S.mode
            c.pop("min_rerank", None)
            msg.append("tryb: " + ("ostrożny" if S.mode == "careful" else "zwykły"))
        if body.get("gpu") in ("auto", "cpu"):
            c["gpu"] = body["gpu"]
            msg.append("karta graficzna: " + ("automatycznie" if body["gpu"] == "auto" else "wyłączona")
                       + " (od następnego uruchomienia)")
        if body.get("threads"):
            t = max(1, min(int(body["threads"]), os.cpu_count() or 8))
            c["threads"] = t
            msg.append(f"wątki: {t} (od następnego uruchomienia)")
        if body.get("documents"):
            p = Path(str(body["documents"])).expanduser()
            if not p.is_dir():
                return self._send(400, {"error": "Taki folder nie istnieje."})
            if S.job["busy"]:
                return self._send(409, {"error": "Indeksowanie już trwa."})
            reindex(p)
            msg.append("folder: " + str(p))
        save_cfg(c)
        log("ustawienia:", "; ".join(msg) or "bez zmian")
        return self._send(200, {"ok": True, "message": "; ".join(msg), **settings_dict()})

    def _upload(self):
        name = webapi.safe_upload_name(unquote(self.headers.get("X-Filename", "")))
        n = int(self.headers.get("Content-Length", "0") or 0)
        if not name or n <= 0 or n > 50 * 1024 * 1024:
            return self._send(400, {"error": "Dozwolone dokumenty: .pdf, .docx, .odt, .txt, .md, .rtf, .html, .htm, .epub, .pptx, .xlsx, .csv, .tsv (do 50 MB; .doc/.odp/.ods zapisz jako .docx albo .odt)."})
        data = self.rfile.read(n)
        with S.lock:
            docs = S.docs.resolve()
            dst = (docs / name).resolve()
            if dst.parent != docs:
                return self._send(400, {"error": "Niedozwolona nazwa pliku."})
            if dst.exists():
                return self._send(409, {"error": f"Plik {name} już jest w folderze dokumentów."})
            dst.write_bytes(data)
        job = S.uploads.submit(dst, name)
        log("w kolejce:", name, round(n / 1e6, 2), "MB")
        return self._send(202, {"ok": True, "job": job})


if __name__ == "__main__":
    url = start()
    if not os.environ.get("SEJF_NO_BROWSER"):
        import webbrowser
        webbrowser.open(url)
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        stop()
