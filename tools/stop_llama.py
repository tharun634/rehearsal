"""Stop a llama-server left resident by an interrupted run.

`record_demo.py` stops the server itself, but a run killed mid-session (a
timeout, a Ctrl-C in the wrong shell) leaves a 2.6 GB model holding RAM and
VRAM on a machine that has almost neither. This is the one command that puts it
back. Windows-only, stdlib-only: `taskkill` through a shell mangles `/F` into a
path on git-for-windows, so the argv is built here, not in the shell.
"""
import subprocess
import sys

# argv, not a shell string: cmd would rewrite /F as a Windows path
CMD = ["taskkill", "/F", "/IM", "llama-server.exe"]
p = subprocess.run(CMD, capture_output=True, text=True)
print(p.stdout.strip() or p.stderr.strip())
sys.exit(0 if p.returncode == 0 else (1 if "not found" not in p.stderr else 0))
