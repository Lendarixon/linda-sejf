"""Weryfikator Sejfu w runtime: ONNX int8 + tokenizer.json (biblioteka `tokenizers`), bez `transformers`.

Niezależny od wersji transformers (tokenizer zapisany na Kaggle przez transformers 5 nie wczytuje się w 4.x).
Katalog modelu: model_int8.onnx, tokenizer.json, sejf_verifier.json (próg, nazwa).
"""
from __future__ import annotations

import json
from pathlib import Path


def load(model_dir: str | Path, threads: int = 4, max_length: int = 512):
    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer

    d = Path(model_dir)
    cfg = json.loads((d / "sejf_verifier.json").read_text(encoding="utf-8")) if (d / "sejf_verifier.json").exists() else {}
    tok = Tokenizer.from_file(str(d / "tokenizer.json"))
    tok.enable_truncation(max_length=max_length, strategy="only_second")
    pad_id = tok.token_to_id("<pad>")
    if pad_id is None:
        pad_id = 1
    tok.enable_padding(pad_id=pad_id, pad_token=tok.id_to_token(pad_id) or "<pad>")
    so = ort.SessionOptions()
    so.intra_op_num_threads = threads
    sess = ort.InferenceSession(str(d / "model_int8.onnx"), so, providers=["CPUExecutionProvider"])
    names = {i.name for i in sess.get_inputs()}

    def score(pairs, batch: int = 16):
        out = []
        for i in range(0, len(pairs), batch):
            b = pairs[i:i + batch]
            enc = tok.encode_batch([(a, s) for a, s in b])
            feed = {}
            if "input_ids" in names:
                feed["input_ids"] = np.array([e.ids for e in enc], dtype=np.int64)
            if "attention_mask" in names:
                feed["attention_mask"] = np.array([e.attention_mask for e in enc], dtype=np.int64)
            if "token_type_ids" in names:
                feed["token_type_ids"] = np.array([e.type_ids for e in enc], dtype=np.int64)
            lo = sess.run(None, feed)[0]
            ex = np.exp(lo - lo.max(-1, keepdims=True))
            out += (ex[:, 1] / ex.sum(-1)).tolist()
        return out

    return score, float(cfg.get("threshold", 0.5)), cfg
