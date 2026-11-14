"""Pobiera modele Linda Sejf z Hugging Face (przypięte rewizje, sprawdzanie sha256, wznawianie przerwanego pobierania).

  Gemma-4-E4B-it Q6_K (unsloth, Apache-2.0)            ok. 7,1 GB
  weryfikator zdań HerBERT ONNX int8 (CC BY 4.0)        ok. 125 MB
  multilingual-e5-small ONNX (MIT)                      ok. 470 MB
  polish-reranker-base-ranknet ONNX (Apache-2.0)        ok. 500 MB

Użycie: python tools/download_models.py [folder_modeli]   (domyślnie ./models)
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

GEMMA_REV = "bfc15c382204943c3a8fff0c750b94ae2364d7a3"
SEJF_REV = "a9946978e012bab9b81282eca26d94b93e5217ad"
HF = "https://huggingface.co"
FILES = [
    (f"{HF}/unsloth/gemma-4-E4B-it-GGUF/resolve/{GEMMA_REV}/gemma-4-E4B-it-Q6_K.gguf", "gemma-4-E4B-it-Q6_K.gguf",
     "fd83f3ef44d22e00ff0f638753dde9a66a83e8ccf79c11024f47d383c489531b"),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/verifier/model_int8.onnx", "verifier/model_int8.onnx",
     "93be4abcc291a39af150dd1d47d21011a3d72e0f7af934a2512031791681f340"),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/verifier/tokenizer.json", "verifier/tokenizer.json", None),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/verifier/sejf_verifier.json", "verifier/sejf_verifier.json", None),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/onnx/e5/model.onnx", "e5/model.onnx",
     "ccc031fa62ca16aea08705940b23f3d3d8250fdabd8537c26bb2ab0bd87db9fc"),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/onnx/e5/tokenizer.json", "e5/tokenizer.json",
     "41621bfd5ef0f4b2914cb0224f08a63a208ff71283fee803bfd251e2e2b7388d"),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/onnx/reranker/model.onnx", "reranker/model.onnx",
     "017d6d90036717834014834ec8fa307ab84e7ff10521cf2c822b3a6da9eda6ac"),
    (f"{HF}/Lindarixon/Linda-Sejf/resolve/{SEJF_REV}/onnx/reranker/tokenizer.json", "reranker/tokenizer.json",
     "6ec6a058dd366c0337aaf7c31d4cb7ae274e94bc690e42fcc182c9aca975f518"),
]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch(url: str, dst: Path, progress=None):
    part = dst.with_name(dst.name + ".part")
    have = part.stat().st_size if part.exists() else 0
    req = urllib.request.Request(url, headers={"User-Agent": "linda-sejf-installer", **({"Range": f"bytes={have}-"} if have else {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        if have and r.status != 206:
            have = 0
        total = have + int(r.headers.get("Content-Length", 0))
        with open(part, "ab" if have else "wb") as f:
            done, last = have, -1
            while True:
                b = r.read(1 << 20)
                if not b:
                    break
                f.write(b)
                done += len(b)
                pct = int(done * 100 / total) if total else 0
                if pct != last:
                    print(f"\r  {dst.name}: {pct}% ({done >> 20} / {total >> 20} MB)", end="", flush=True)
                    if progress:
                        progress(f"Pobieram {dst.name}: {pct}% ({done >> 20} z {total >> 20} MB)")
                    last = pct
    print()
    part.replace(dst)


def main(root=None, progress=None):
    """Pobiera brakujące modele; progress(tekst) — opcjonalny raport postępu (okno programu)."""
    root = Path(root or (sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "models"))
    for url, rel, sha in FILES:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if progress:
            progress(f"Sprawdzam {rel}…")
        if dst.exists() and (sha is None or sha256(dst) == sha):
            print("  jest:", rel)
            continue
        print("Pobieram", rel)
        for attempt in range(3):
            try:
                fetch(url, dst, progress)
                break
            except Exception as e:
                print(f"\n  przerwane ({e}); ponawiam {attempt + 1}/3")
        else:
            raise RuntimeError(f"Nie udało się pobrać {rel}. Sprawdź internet i uruchom program ponownie.")
        if sha and sha256(dst) != sha:
            dst.unlink()
            raise RuntimeError(f"Suma kontrolna {rel} się nie zgadza — plik usunięty, uruchom program ponownie.")
    print("Modele gotowe w", root)


if __name__ == "__main__":
    main()
