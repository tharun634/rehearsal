"""One command: check the machine, run a real session, write the evidence.

This is the demo recorder for the write-up. It does four things in order:

  1. reads the machine (total / free RAM) BEFORE anything is loaded, so the
     numbers in the post carry the honest caveat;
  2. starts llama-server as a CHILD of this script, so it is gone when the
     script exits — nothing is left resident holding your RAM;
  3. runs `rehearsal practice` exactly as you would type it, streaming the
     console to the screen AND into docs/demos/<name>.txt (the terminal tape
     you embed in the DEV post);
  4. writes docs/research/<date>-<tag>-record.md with the commands, the timings,
     the token counts and the RAM at the moment of the run (the tag is in the
     filename so a scratch run cannot overwrite a real one).

Usage:
  python tools/record_demo.py --scenario cafe-aoi --interactive
  python tools/record_demo.py --scenario cafe-aoi --script docs/demos/script-cafe-aoi.txt
  python tools/record_demo.py --scenario cafe-aoi --both        # server AND cli, back to back
  python tools/record_demo.py --scenario cafe-aoi --engine mock # plumbing check, no model

Exit code 0 means the evidence files were written, not that the friend
spoke well. Read the tape.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
import urllib.request
from urllib.error import URLError
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rehearsal.console import utf8_console      # noqa
from rehearsal.engine import load_engine_config  # noqa
from rehearsal.memory import connect             # noqa

CONFIG_ENGINE = "config/engine.toml"


# --------------------------------------------------------------------------- #
# machine facts, stdlib only
# --------------------------------------------------------------------------- #
def ram_mb() -> tuple[int, int]:
    """(total, available) physical memory in MB, read from `systeminfo`.
    Slow (tens of seconds) but stdlib-honest: ctypes.GetSystemInfo is not
    reachable in this Python build (ntdll does not export the name), and a
    wrong RAM figure in the post would be worse than a slow one. Returns
    (0, 0) if the read fails, and the evidence file says so — or pass
    --ram-total/--ram-free from Task Manager if you already know."""
    vals: dict[str, int] = {}
    for exe in ("systeminfo", "C:/Windows/System32/systeminfo.exe"):
        try:
            out = subprocess.run([exe], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace", timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            continue
        for ln in (out.stdout + out.stderr).splitlines():
            m = re.match(r"\s*(Total Physical Memory|Available Physical Memory)\s*:\s*([\d.,]+)", ln)
            if m:
                vals[m.group(1)] = int(m.group(2).replace(",", "").replace(".", ""))
        if vals:
            break
    # systeminfo already reports megabytes; shifting them as if they were
    # bytes is how this read used to print 0.
    return (vals.get("Total Physical Memory", 0),
            vals.get("Available Physical Memory", 0))


def speed_lines(text: str) -> list[str]:
    """llama-cli's own speed lines, kept verbatim as evidence."""
    return [ln.strip() for ln in text.splitlines()
            if "t/s" in ln and ("Prompt" in ln or "eval" in ln or "n_eval" in ln)]


def run_cli(argv: list[str]) -> tuple[int, str]:
    """Run `python run.py ...` streaming to screen and returning the tape."""
    parts: list[str] = []
    proc = subprocess.Popen([sys.executable, str(ROOT / "run.py")] + argv,
                            cwd=str(ROOT), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace")
    for line in proc.stdout:
        print(line.rstrip("\n"), flush=True)
        parts.append(line)
    return proc.wait(), "".join(parts)


def wait_for_server(port: int, timeout_s: int = 240) -> bool:
    url = f"http://127.0.0.1:{port}/health"
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except (URLError, OSError, ValueError):
            time.sleep(2)
    return False


def main() -> int:
    utf8_console()
    import argparse
    ap = argparse.ArgumentParser(description="record a demo and its measurements")
    ap.add_argument("--scenario", default="cafe-aoi")
    ap.add_argument("--turns", type=int, default=5)
    ap.add_argument("--script", help="file of learner lines, one per line (hands-free demo)")
    ap.add_argument("--interactive", action="store_true", help="type your own lines")
    ap.add_argument("--both", action="store_true", help="measure server mode AND cli mode")
    ap.add_argument("--engine", default="server", choices=["server", "cli", "mock"])
    ap.add_argument("--tag", default=None, help="name for the evidence files")
    ap.add_argument("--ram-total", type=int, help="MB total, if systeminfo is too slow")
    ap.add_argument("--ram-free", type=int, help="MB free, from Task Manager")
    a = ap.parse_args()

    tag = a.tag or a.scenario
    stamp = datetime.now().strftime("%Y-%m-%d")
    eng_cfg = load_engine_config(CONFIG_ENGINE)
    port = int(str(eng_cfg["base_url"]).rsplit(":", 1)[-1])

    total, avail = ram_mb()
    if a.ram_total:
        total = a.ram_total
    if a.ram_free:
        avail = a.ram_free
    tight = 0 < avail < 4000
    print(f"machine: {total} MB total, {avail} MB free "
          f"({'TIGHT — close the other model first' if tight else 'roomy'})")
    if total == 0:
        print("note: the RAM read failed; the evidence file will say RAM unknown")

    modes = ["server", "cli"] if a.both else [a.engine]
    runs: list[dict] = []
    server_proc = None

    for mode in modes:
        if mode == "server" and a.engine != "mock":
            exe = eng_cfg["llama_server"]
            if not exe:
                print("no llama_server path in config/engine.toml — run tools/get_llama.py")
                return 1
            log = open(ROOT / "logs" / f"llama-server-{stamp}.log", "w", encoding="utf-8")
            server_proc = subprocess.Popen(
                [exe, "-m", eng_cfg["gguf"], "--ctx-size", str(eng_cfg["ctx"]),
                 "-ngl", str(eng_cfg["ngl"]), "--port", str(port),
                 "--temp", str(eng_cfg["temperature"])],
                cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT)
            print(f"llama-server starting on port {port} (child of this script; "
                  f"it is stopped below)")
            if not wait_for_server(port):
                print("llama-server never answered /health — see logs/")
                server_proc.terminate()
                server_proc.wait(timeout=60)
                return 1
            print("server is up; the session runs now")

        argv = ["practice", "--scenario", a.scenario, "--turns", str(a.turns),
                "--engine", mode]
        name = f"{tag}-{mode}-{stamp}"
        if a.script:
            argv += ["--script", a.script]
        argv += ["--transcript", f"docs/transcripts/{name}.md"]
        code, tape = run_cli(argv)
        (ROOT / "docs" / "demos").mkdir(parents=True, exist_ok=True)
        tape_path = ROOT / "docs" / "demos" / f"{name}.txt"
        tape_path.write_text(tape, encoding="utf-8")
        runs.append({"mode": mode, "code": code, "tape": str(tape_path),
                     "tps": speed_lines(tape)})

        if mode == "server" and server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=60)
            print("llama-server stopped — nothing resident now")
            time.sleep(2)

    # ---- the evidence file ---------------------------------------------------- #
    out = ROOT / "docs" / "research" / f"{stamp}-{tag}-record.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Record — {stamp}", "",
             f"- RAM at start: {total} MB total / {avail} MB free"
             if total else "- RAM at start: read failed (see `systeminfo`)",
             f"- model: {eng_cfg['gguf']}",
             f"- llama-server: {eng_cfg['llama_server'] or '(not fetched)'}",
             f"- llama-cli: {eng_cfg['llama_cli'] or '(not fetched)'}",
             f"- ctx {eng_cfg['ctx']} · ngl {eng_cfg['ngl']} · temp {eng_cfg['temperature']}",
             "", "## Runs", ""]
    for r in runs:
        lines += [f"### {r['mode']}", f"- exit: {r['code']}",
                  f"- tape: `{r['tape']}`",
                  f"- transcript: `docs/transcripts/{tag}-{r['mode']}-{stamp}.md`",
                  f"- llama.cpp speed lines: {r['tps'] or '(server mode: the transcript table carries the timings)'}",
                  ""]
    lines += ["## What this does NOT prove",
              "- the RAM figure is read before the model loads; if another model was",
              "  resident, llama.cpp paged against the page file and every number below",
              "  is a floor, not the machine's real speed.", ""]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nevidence: {out}")
    for r in runs:
        print(f"tape:     {r['tape']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
