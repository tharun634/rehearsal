"""get_model.py — fetch a Gemma GGUF for local inference.

Gemma 3 is Google's open-weight model: it downloads as a file, runs in llama.cpp,
and can be fine-tuned or swapped by the user. Nothing here signs in or phones home.

    python tools/get_model.py                    # gemma-3-4b-it Q4_K_M (~2.6 GB)
    python tools/get_model.py --model gemma-3-1b # ~0.8 GB, for a tight laptop
    python tools/get_model.py --quant Q8_0       # any quant the repo carries

Weights are gitignored (models/); this script is the artifact.
"""
import argparse
import urllib.request
from pathlib import Path

MODELS = {
    "gemma-3-4b": "unsloth/gemma-3-4b-it-GGUF",
    "gemma-3-12b": "unsloth/gemma-3-12b-it-GGUF",
    "gemma-3-1b": "unsloth/gemma-3-1b-it-GGUF",
}
CHUNK = 1 << 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gemma-3-4b", choices=sorted(MODELS))
    ap.add_argument("--quant", default="Q4_K_M")
    ap.add_argument("--repo", default=None, help="override: any HF repo id holding GGUFs")
    ap.add_argument("--file", default=None, help="override: exact GGUF filename")
    ap.add_argument("--dest", default="models")
    args = ap.parse_args()

    repo = args.repo or MODELS[args.model]
    fname = args.file or f"{args.model}-it-{args.quant}.gguf"
    url = f"https://huggingface.co/{repo}/resolve/main/{fname}"
    dest = Path(args.dest) / fname
    dest.parent.mkdir(parents=True, exist_ok=True)

    print(f"{url}\n  -> {dest}")
    tmp = dest.with_suffix(".gguf.part")
    done = 0
    with urllib.request.urlopen(url, timeout=60) as fh, tmp.open("wb") as out:
        total = int(fh.headers.get("content-length") or 0)
        while True:
            block = fh.read(CHUNK)
            if not block:
                break
            out.write(block)
            done += len(block)
            if total:
                print(f"\r  {done/1e9:.2f} / {total/1e9:.2f} GB", end="", flush=True)
    tmp.rename(dest)
    print(f"\n  {dest}  {dest.stat().st_size/1e9:.2f} GB")


if __name__ == "__main__":
    main()
