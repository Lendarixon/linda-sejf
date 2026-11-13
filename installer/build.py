"""Buduje dist/LindaSejf-Setup-<wersja>.exe (Inno Setup 6).

Wymaga (ścieżki przez argumenty): rozpakowanego Pythona 3.12 embeddable z pakietami (runtime/),
folderu z llama.cpp dla Windows (llama-server.exe + DLL), Inno Setup 6 (ISCC.exe).
Przygotowanie runtime:  python -m pip install --target runtime/Lib/site-packages --only-binary=:all: \
    --python-version 3.12 --platform win_amd64 --implementation cp numpy onnxruntime tokenizers pypdf python-docx
Użycie: python installer/build.py --runtime <dir> --llama <dir> [--iscc <ISCC.exe>] [--version 1.0.0]
"""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_FILES = ["app.py", "launcher.py", "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"]
APP_DIRS = ["sejf", "ui", "tools", "corpus"]
LLAMA_KEEP = ("llama-server.exe", "llama-server-impl.dll", "llama-common.dll", "llama.dll", "mtmd.dll", "libomp.dll")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runtime", required=True, type=Path)
    ap.add_argument("--llama", required=True, type=Path)
    ap.add_argument("--iscc", type=Path, default=Path(os.environ["LOCALAPPDATA"]) / "Programs/Inno Setup 6/ISCC.exe")
    ap.add_argument("--version", default="1.0.0")
    a = ap.parse_args()
    pay = ROOT / "build" / "payload"
    if pay.exists():
        shutil.rmtree(pay)
    pay.mkdir(parents=True)
    for f in APP_FILES:
        shutil.copy2(ROOT / f, pay / f)
    ign = shutil.ignore_patterns("__pycache__", "*.pyc", "validate_*.json", "validate_*.log")
    for d in APP_DIRS:
        shutil.copytree(ROOT / d, pay / d, ignore=ign)
    shutil.copytree(a.runtime, pay / "runtime", ignore=ign)
    (pay / "bin").mkdir()
    for f in a.llama.iterdir():
        if f.name in LLAMA_KEEP or (f.name.startswith("ggml") and f.suffix == ".dll") or f.name.startswith("LICENSE"):
            shutil.copy2(f, pay / "bin" / f.name)
    n = sum(1 for _ in pay.rglob("*") if _.is_file())
    print("payload:", n, "plików")
    subprocess.run([str(a.iscc), f"/DAppVersion={a.version}", f"/DPayload={pay}", str(ROOT / "installer" / "linda_sejf.iss")], check=True)
    print("gotowe:", ROOT / "dist" / f"LindaSejf-Setup-{a.version}.exe")


if __name__ == "__main__":
    main()
