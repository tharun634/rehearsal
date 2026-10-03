"""get_llama.py — fetch llama.cpp's own prebuilt Windows binaries.

The repo needs two executables and nothing else from llama.cpp: llama-server.exe
(fast path) and llama-cli.exe (the mode that keeps nothing resident). This is one
download, no model registry, no second runtime.

    python tools/get_llama.py                 # latest release, Vulkan build
    python tools/get_llama.py --build cpu     # CPU-only build, no GPU driver needed
    python tools/get_llama.py --write-config  # also point config/engine.toml at them

Binaries are gitignored (tools/*.exe, tools/*.zip); this script is the artifact.
"""
import argparse
import json
import urllib.request
import zipfile
from pathlib import Path

API = "https://api.github.com/repos/ggml-org/llama.cpp/releases"
UA = {"User-Agent": "rehearsal-get-llama"}


def _pick(releases, build, ref):
    for r in releases:
        if ref != "latest" and r["tag_name"] != ref:
            continue
        for a in r["assets"]:
            n = a["name"]
            if n.startswith("llama-") and "bin-win" in n and n.endswith(".zip"):
                if f"-{build}-" in n and ("x64" in n or "arm64" in n):
                    return r, a
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default="vulkan", help="vulkan | cpu | cuda | sycl | openvino")
    ap.add_argument("--ref", default="latest", help="release tag, e.g. b11379")
    ap.add_argument("--dest", default="tools/bin")
    ap.add_argument("--write-config", action="store_true")
    args = ap.parse_args()

    rel = json.load(urllib.request.urlopen(urllib.request.Request(API, headers=UA), timeout=30))
    r, a = _pick(rel, args.build, args.ref)
    if not a:
        raise SystemExit(f"no bin-win zip for build={args.build} in the first {len(rel)} releases")

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / a["name"]
    print(f"{r['tag_name']}  {a['name']}  {a['size']/1e6:.0f} MB")

    with urllib.request.urlopen(a["browser_download_url"], timeout=60) as fh:
        zip_path.write_bytes(fh.read())

    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if n.endswith(".exe")]
        z.extractall(dest)
    zip_path.unlink()

    want = ["llama-server.exe", "llama-cli.exe"]
    found = {}
    for exe in want:
        hits = sorted((dest / n).name for n in names if n.endswith(exe))
        if not hits:
            print(f"  MISSING {exe} in this build")
            continue
        found[exe] = dest / hits[-1]      # newest path wins if duplicated
        print(f"  {found[exe]}")

    if args.write_config:
        cfg = Path("config/engine.toml")
        text = cfg.read_text(encoding="utf-8")
        for key, exe in (("llama_server", "llama-server.exe"), ("llama_cli", "llama-cli.exe")):
            if exe in found:
                p = str(found[exe]).replace("\\", "/")
                text = _set_key(text, key, p)
        cfg.write_text(text, encoding="utf-8")
        print(f"  wrote paths into {cfg}")


def _set_key(text, key, value):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{key}"):
            lines[i] = f'{key} = "{value}"'
            break
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


if __name__ == "__main__":
    main()
