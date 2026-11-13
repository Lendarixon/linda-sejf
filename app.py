"""Linda Sejf — lokalna aplikacja (Windows/Linux). Serwer HTTP na 127.0.0.1, interfejs w przeglądarce.

Przepływ: wyszukiwarka (e5 + BM25 + polski reranker, ONNX) -> bramka odmowy (reranker < 0,9 = odmowa bez modelu)
-> model językowy w llama.cpp (domyślnie Gemma-4-E4B Q6_K) -> weryfikator zdań (HerBERT, ONNX int8) -> dziennik audytu.
Nic nie jest wysyłane do internetu; połączenia tylko do lokalnego llama-server.

Konfiguracja: config.json obok tego pliku (tworzony przy pierwszym starcie) albo zmienne środowiskowe:
  SEJF_DOCS   folder z dokumentami (.txt, .md, .pdf, .docx)       SEJF_MODELS  folder z modelami
  SEJF_GGUF   plik modelu GGUF                                     SEJF_LLAMA   ścieżka do llama-server
  SEJF_PORT   port (domyślnie 8765)                                 SEJF_MIN_RERANK  próg bramki (0 = wyłączona)
  SEJF_THREADS  wątki CPU                                           SEJF_NO_BROWSER=1  nie otwieraj przeglądarki
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from sejf import Sejf, verifier_onnx  # noqa: E402
from sejf.retriever_simple import Index, make_retriever  # noqa: E402

DATA = Path(os.environ.get("SEJF_DATA", Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LindaSejf"))
DATA.mkdir(parents=True, exist_ok=True)
CFG_P = DATA / "config.json"
cfg = json.loads(CFG_P.read_text(encoding="utf-8")) if CFG_P.exists() else {}


def opt(key, env, default):
    if os.environ.get(env) not in (None, ""):
        return os.environ[env]
    return cfg[key] if cfg.get(key) is not None else default


MODELS = Path(opt("models", "SEJF_MODELS", HERE / "models"))
DOCS = Path(opt("documents", "SEJF_DOCS", HERE / "corpus"))
GGUF = Path(opt("gguf", "SEJF_GGUF", MODELS / "gemma-4-E4B-it-Q6_K.gguf"))
exe = "llama-server.exe" if os.name == "nt" else "llama-server"
LLAMA = Path(opt("llama", "SEJF_LLAMA", HERE / "bin" / exe))
PORT = int(opt("port", "SEJF_PORT", 8765))
THREADS = int(opt("threads", "SEJF_THREADS", max(2, (os.cpu_count() or 4) // 2)))
MIN_RERANK = float(opt("min_rerank", "SEJF_MIN_RERANK", 0.975))
LLAMA_PORT = PORT + 1
if not CFG_P.exists():
    CFG_P.write_text(json.dumps({"documents": str(DOCS), "models": str(MODELS), "gguf": str(GGUF), "port": PORT,
                                 "threads": THREADS, "min_rerank": MIN_RERANK}, ensure_ascii=False, indent=1), encoding="utf-8")


def log(*a):
    line = time.strftime("%H:%M:%S") + " " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(DATA / "sejf.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


missing = [str(p) for p in (GGUF, LLAMA, MODELS / "e5" / "model.onnx", MODELS / "reranker" / "model.onnx",
                            MODELS / "verifier" / "model_int8.onnx") if not p.exists()]
if missing:
    log("Brak plików:", *missing)
    log("Uruchom pobieranie modeli: python tools/download_models.py  (instalator robi to sam)")
    sys.exit(2)

log("Linda Sejf: dokumenty", DOCS)
t = time.time()
index = Index(DOCS, MODELS, DATA / "state", threads=THREADS)
log("indeks gotowy:", len(index.meta), "fragmentów,", round(time.time() - t, 1), "s")
retrieve = make_retriever(index)

flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
llama = subprocess.Popen([str(LLAMA), "-m", str(GGUF), "--host", "127.0.0.1", "--port", str(LLAMA_PORT), "-c", "6144",
                          "-t", str(THREADS), "-tb", str(THREADS), "--temp", "0", "-np", "1", "--jinja", "--no-webui"],
                         stdout=open(DATA / "llama.log", "ab"), stderr=subprocess.STDOUT, creationflags=flags)
for _ in range(600):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{LLAMA_PORT}/health", timeout=2)
        break
    except Exception:
        if llama.poll() is not None:
            log("llama-server zakończył się błędem, zobacz", DATA / "llama.log")
            sys.exit(3)
        time.sleep(1)
log("model gotowy:", GGUF.name)


def generate(messages):
    body = json.dumps({"messages": messages, "temperature": 0, "max_tokens": 350, "cache_prompt": True,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{LLAMA_PORT}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


vfn, vthr, vcfg = verifier_onnx.load(MODELS / "verifier", threads=THREADS)
sejf = Sejf(retrieve, generate, vfn, threshold=vthr, mode="flag", k=5, min_rerank_score=MIN_RERANK or None,
            audit_path=DATA / "sejf_audit.jsonl", model_info={"generator": GGUF.name, "verifier": vcfg.get("name")})
INDEX_HTML = (HERE / "ui" / "index.html").read_bytes()
gen_lock = threading.Lock()


class H(BaseHTTPRequestHandler):
    server_version = "LindaSejf/1.0"

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                                                    "script-src 'self' 'unsafe-inline'; img-src 'self' data:")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *a):
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self._send(200, INDEX_HTML, "text/html; charset=utf-8")
        if self.path == "/api/health":
            return self._send(200, {"ok": True, "model": GGUF.name, "verifier": vcfg.get("name"), "documents": str(DOCS),
                                    "chunks": len(index.meta), "min_rerank": MIN_RERANK, "threads": THREADS, "local": True})
        return self._send(404, {"error": "not-found"})

    def do_POST(self):
        if self.path != "/api/ask":
            return self._send(404, {"error": "not-found"})
        if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            return self._send(403, {"error": "origin"})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(n)) if 0 < n <= 8192 else {}
            q = str(body.get("question", "")).strip()
            mode = "strict" if body.get("mode") == "strict" else "flag"
        except Exception:
            return self._send(400, {"error": "bad-json"})
        if not q or len(q) > 1000:
            return self._send(400, {"error": "Pytanie musi mieć od 1 do 1000 znaków."})
        try:
            with gen_lock:
                t0 = time.time()
                a = sejf.ask(q, user="local", mode=mode)
                dt = time.time() - t0
            d = a.to_dict()
            d["seconds"] = round(dt, 1)
            log("pytanie:", a.status, round(dt, 1), "s")
            return self._send(200, d)
        except Exception as e:
            log("błąd", type(e).__name__, str(e)[:300])
            return self._send(500, {"error": "Błąd aplikacji, zobacz sejf.log."})


url = f"http://127.0.0.1:{PORT}/"
log("gotowe:", url)
if not os.environ.get("SEJF_NO_BROWSER"):
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
try:
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
finally:
    llama.terminate()
