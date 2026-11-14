"""Start Linda Sejf w oknie programu (WebView2 przez pywebview). Bez WebView2 — w przeglądarce.

Przy pierwszym uruchomieniu pobiera modele (ok. 8,2 GB) i buduje indeks; postęp widać w oknie.
Zamknięcie okna zatrzymuje program (także model językowy).
"""
import json
import os
import runpy
import subprocess
import sys
import threading
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))
ICON = HERE / "ui" / "linda.ico"
TITLE = "Linda Sejf"

LOADING = """<!doctype html><html lang="pl"><head><meta charset="utf-8"><style>
html,body{margin:0;height:100%;background:#0d0f15;color:#fff;font:15px/1.5 "Segoe UI",sans-serif}
.w{height:100%;display:flex;flex-direction:column;justify-content:center;padding:0 12%}
h1{font:300 54px/1 "Segoe UI Variable Display","Segoe UI",sans-serif;margin:0 0 12px;letter-spacing:-.02em}
p{color:#c3c8d2;margin:0 0 28px;max-width:620px}
.bar{height:4px;background:#1f232d;overflow:hidden;max-width:620px}.bar i{display:block;height:100%;width:30%;background:#2f6fe6;animation:m 1.4s ease-in-out infinite}
@keyframes m{0%{transform:translateX(-100%)}100%{transform:translateX(340%)}}
#st{margin-top:14px;color:#8fb3ff;font-size:14px}.err #st{color:#ff8a8a}.err .bar{display:none}
</style></head><body><div class="w" id="w"><h1>linda sejf</h1>
<p>Twoje dokumenty zostają na tym komputerze. Pierwsze uruchomienie pobiera modele i buduje indeks — to zdarza się tylko raz.</p>
<div class="bar"><i></i></div><div id="st">Uruchamiam…</div></div>
<script>function setStatus(t,e){document.getElementById('st').textContent=t;if(e)document.getElementById('w').className='w err'}</script>
</body></html>"""


class Api:
    """Funkcje dostępne z interfejsu: wybór folderu i otwieranie folderów w Eksploratorze."""

    def __init__(self):
        self._window = None

    def pick_folder(self):
        import webview
        mode = getattr(getattr(webview, "FileDialog", None), "FOLDER", None) or webview.FOLDER_DIALOG
        paths = self._window.create_file_dialog(mode)
        return str(paths[0]) if paths else ""

    def open_folder(self, which):
        """which: 'docs' albo 'data' — żadnych dowolnych ścieżek z interfejsu (np. udziałów sieciowych)."""
        import app
        p = {"docs": app.S.docs, "data": app.DATA, "notes": app.DATA / "notatki"}.get(str(which))
        if p is None or not Path(p).is_dir() or str(p).startswith("\\\\") or os.name != "nt":
            return False
        os.startfile(str(p))  # noqa: S606
        return True


def run_window():
    import webview

    api = Api()
    window = webview.create_window(TITLE, html=LOADING, width=1360, height=860, min_size=(900, 600),
                                   background_color="#0d0f15", text_select=True, js_api=api)
    api._window = window

    def status(text, error=False):
        try:
            window.evaluate_js(f"setStatus({json.dumps(str(text))},{'true' if error else 'false'})")
        except Exception:
            pass

    def boot():
        try:
            import app
            if app.missing_files():
                status("Pobieram modele (ok. 8,2 GB, jednorazowo)…")
                import importlib.util
                spec = importlib.util.spec_from_file_location("download_models", HERE / "tools" / "download_models.py")
                dm = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(dm)
                dm.main(app.MODELS, progress=status)
            url = app.start(status=status)
            window.load_url(url)
        except Exception as e:
            traceback.print_exc()
            status(f"Nie udało się uruchomić: {e}", error=True)

    def closing():
        try:
            import app
            app.stop()
        except Exception:
            pass

    window.events.closing += closing
    opts = {"gui": "edgechromium", "debug": False}
    if ICON.is_file():
        opts["icon"] = str(ICON)
    try:
        webview.start(boot, **opts)
    except TypeError:
        opts.pop("icon", None)
        webview.start(boot, **opts)


def run_browser():
    """Zapas bez WebView2: konsola + przeglądarka."""
    import app
    if app.missing_files():
        print("Linda Sejf — pierwsze uruchomienie: pobieram modele (ok. 8,2 GB, jednorazowo).\n")
        sys.argv = ["download_models.py", str(app.MODELS)]
        runpy.run_path(str(HERE / "tools" / "download_models.py"), run_name="__main__")
    sys.argv = ["app.py"]
    runpy.run_path(str(HERE / "app.py"), run_name="__main__")


if __name__ == "__main__":
    log = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LindaSejf" / "launcher.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    if sys.stdout is None or "pythonw" in Path(sys.executable).name.lower():
        sys.stdout = sys.stderr = open(log, "a", encoding="utf-8", buffering=1)
    try:
        if "--browser" in sys.argv:
            raise ImportError("tryb przeglądarki")
        run_window()
    except Exception:  # brak pywebview / WebView2 — zapasowo przeglądarka
        traceback.print_exc()
        if "pythonw" in Path(sys.executable).name.lower():
            subprocess.Popen([str(Path(sys.executable).with_name("python.exe")), str(Path(__file__)), "--browser"])
        else:
            run_browser()
