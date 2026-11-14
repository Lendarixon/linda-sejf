"""ui/index.src.html + logo -> ui/index.html (logo osadzone jako data URI, bo CSP blokuje zewnętrzne zasoby)."""
import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE / "index.src.html").read_text(encoding="utf-8")
logo = "data:image/png;base64," + base64.b64encode((HERE / "logo.png").read_bytes()).decode()
(HERE / "index.html").write_text(src.replace("__LOGO__", logo), encoding="utf-8")
print("ok", len(src))
