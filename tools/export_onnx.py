"""Eksport modeli wyszukiwania do ONNX (bez PyTorch w produkcie).

- intfloat/multilingual-e5-small  -> models/e5/model.onnx + tokenizer.json   (embedding, mean pooling w runtime)
- sdadas/polish-reranker-base-ranknet -> models/reranker/model.onnx + tokenizer.json (logit; runtime liczy sigmoid)

Uruchomienie (potrzebne: torch, transformers): python tools/export_onnx.py <katalog_wyjściowy>
"""
import sys
from pathlib import Path

import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "models")


def export(name, sub, cls, out_names):
    d = OUT / sub
    d.mkdir(parents=True, exist_ok=True)
    tok = AutoTokenizer.from_pretrained(name)
    model = cls.from_pretrained(name).eval()
    enc = tok(["query: test", "passage: przykład"], ["", ""] if sub == "reranker" else None,
              padding=True, return_tensors="pt") if sub == "reranker" else tok(["query: test", "passage: przykład"], padding=True, return_tensors="pt")
    inputs = (enc["input_ids"], enc["attention_mask"])
    names = ["input_ids", "attention_mask"]
    dyn = {n: {0: "batch", 1: "seq"} for n in names}
    dyn[out_names[0]] = {0: "batch"} if sub == "reranker" else {0: "batch", 1: "seq"}

    class Wrap(torch.nn.Module):
        def __init__(self, m):
            super().__init__(); self.m = m

        def forward(self, input_ids, attention_mask):
            o = self.m(input_ids=input_ids, attention_mask=attention_mask)
            return o.logits if sub == "reranker" else o.last_hidden_state

    torch.onnx.export(Wrap(model), inputs, str(d / "model.onnx"), input_names=names, output_names=out_names,
                      dynamic_axes=dyn, opset_version=17, dynamo=False)
    tok.backend_tokenizer.save(str(d / "tokenizer.json"))
    (d / "SOURCE.txt").write_text(f"Eksport ONNX modelu https://huggingface.co/{name} (licencja jak w oryginale).\n", encoding="utf-8")
    print("ok", name, "->", d)


export("intfloat/multilingual-e5-small", "e5", AutoModel, ["last_hidden_state"])
export("sdadas/polish-reranker-base-ranknet", "reranker", AutoModelForSequenceClassification, ["logits"])
