"""Free Vedora narration: IndicF5 (ai4bharat, MIT) voice cloning, loaded directly (no transformers AutoModel).
Needs HF_TOKEN in the environment (free account, model terms accepted once).
Usage: python3 vedora_tts.py ref.wav ref_text.txt out_prefix "line 1" "0.8|slower line 2" ...
Writes out_prefix_01.wav, out_prefix_02.wav ... (24 kHz mono), one file per line, so captions can be timed per line.
"""
import glob, os, sys, time
import numpy as np, soundfile as sf, torch
from huggingface_hub import hf_hub_download, snapshot_download
from safetensors.torch import load_file
from f5_tts.infer.utils_infer import infer_process, load_model, load_vocoder, preprocess_ref_audio_text
from f5_tts.model import DiT

import torchaudio
def _sf_load(path, *a, **k):          # new torchaudio needs torchcodec for load(); soundfile does the same job
    data, sr = sf.read(path, dtype="float32", always_2d=True)
    return torch.from_numpy(data.T.copy()), sr
torchaudio.load = _sf_load

torch.set_num_threads(os.cpu_count() or 2)
REPO = "ai4bharat/IndicF5"

def load():
    snap = snapshot_download(REPO, allow_patterns=["model.safetensors", "checkpoints/vocab.txt", "config.json"])
    vocab = os.path.join(snap, "checkpoints", "vocab.txt")
    vocoder = load_vocoder(vocoder_name="vocos", is_local=False, device="cpu")
    model = load_model(DiT, dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4),
                       mel_spec_type="vocos", vocab_file=vocab, device="cpu")
    sd = load_file(os.path.join(snap, "model.safetensors"), device="cpu")
    em = {k[len("ema_model._orig_mod."):]: v for k, v in sd.items() if k.startswith("ema_model._orig_mod.")}
    vo = {k[len("vocoder._orig_mod."):]: v for k, v in sd.items() if k.startswith("vocoder._orig_mod.")}
    r1 = model.load_state_dict(em, strict=False); r2 = vocoder.load_state_dict(vo, strict=False)
    print("missing/unexpected:", len(r1.missing_keys), len(r1.unexpected_keys), len(r2.missing_keys), len(r2.unexpected_keys), flush=True)
    model.eval(); vocoder.eval()
    return model, vocoder

def speak(model, vocoder, ref_audio, ref_text, text, nfe=32, speed=1.0):
    with torch.inference_mode():
        audio, sr, _ = infer_process(ref_audio, ref_text, text, model, vocoder, mel_spec_type="vocos",
                                     nfe_step=nfe, speed=speed, device="cpu", show_info=lambda *a: None)
    return np.asarray(audio, dtype=np.float32), sr

if __name__ == "__main__":
    ref_wav, ref_txt, prefix, *lines = sys.argv[1:]
    t0 = time.time(); model, vocoder = load(); print("loaded in", round(time.time() - t0), "s", flush=True)
    ref_audio, ref_text = preprocess_ref_audio_text(ref_wav, open(ref_txt, encoding="utf-8").read().strip(), show_info=lambda *a: None)
    for i, line in enumerate(lines, 1):
        t0 = time.time()
        speed = 1.0
        if "|" in line[:6]:                      # "0.8|text" = slower delivery (e.g. Sanskrit recitation)
            speed, line = float(line.split("|", 1)[0]), line.split("|", 1)[1]
        a, sr = speak(model, vocoder, ref_audio, ref_text, line, speed=speed)
        sf.write(f"{prefix}_{i:02d}.wav", a, sr)
        print(f"line {i}: {len(a) / sr:.2f}s audio in {time.time() - t0:.0f}s", flush=True)
