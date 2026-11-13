"""Start Linda Sejf z instalatora: przy pierwszym uruchomieniu pobiera modele (ok. 8,2 GB), potem uruchamia aplikację.
Okno konsoli pokazuje postęp; zamknięcie okna zatrzymuje aplikację."""
import os
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
sys.path.insert(0, str(HERE))
models = Path(os.environ.get("SEJF_MODELS", HERE / "models"))
need = [models / "gemma-4-E4B-it-Q6_K.gguf", models / "e5" / "model.onnx", models / "reranker" / "model.onnx",
        models / "verifier" / "model_int8.onnx"]
if not all(p.exists() for p in need):
    print("Linda Sejf — pierwsze uruchomienie: pobieram modele (ok. 8,2 GB, jednorazowo).\n")
    sys.argv = ["download_models.py", str(models)]
    runpy.run_path(str(HERE / "tools" / "download_models.py"), run_name="__main__")
print("\nUruchamiam Linda Sejf (pierwszy start buduje indeks dokumentów, to może potrwać kilka minut)…\n")
sys.argv = ["app.py"]
runpy.run_path(str(HERE / "app.py"), run_name="__main__")
