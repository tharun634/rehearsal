"""Turn this Pi session's jsonl into the normalized agent-session schema DEV
expects, scrubbed, and print the payload size before anything is sent.

DEV's `submit_agent_session` wants {messages: [{role, content: [{type: text |
tool_call, ...}]}], metadata}. Pi's log has roles system/user/assistant/toolResult
and blocks thinking/text/toolCall, so this is a translation, not a copy:

  * toolResult messages are folded into the tool_call that produced them
    (DEV has no toolResult role, and a call without its result is a lie);
  * `thinking` blocks become one short text block, because the reasoning is
    the part judges want to see and the full chain is 245 blocks of noise;
  * machine paths and anything that looks like a token are scrubbed HERE,
    before transmission, not after.

Usage:
  python tools/devrelay_session.py            # write docs/devrelay-session.json
  python tools/devrelay_session.py --check    # print the scrub hits, send nothing
"""
from __future__ import annotations
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- scrubbing #
# The log is full of absolute Windows paths, and one `ls -la` of the home
# directory lists every other project on the machine. None of that belongs on
# a public page, so scrubbing is regex-based, not a list of known prefixes:
# any drive-letter path, any /c/ path, and the username itself.
DRIVE = re.compile(r'''(?i)\b[a-z]:(?:[\\/]{1,4}[A-Za-z0-9_. ()@'"-]+)+''')
MSYS = re.compile(r"/c/(?:[A-Za-z0-9_. ()@'-]+/?)+")
HOME = re.compile(r"(?i)/Users/[A-Za-z0-9_. ()@'-]*(?:/[A-Za-z0-9_. ()@'-]+)*/?")
# Pi names a session folder after the cwd, so the folder name IS the path.
SESSION_DIR = re.compile(r"--C--[A-Za-z0-9-]+--")
USER = re.compile(r"(?i)\btharu\b|tharu\d*")
# Words that only ever appear in a home-directory listing or an absolute path.
# They are a backstop for whatever escaping the log used that the regexes above
# missed; a hit here means the payload still names the machine.
LEAKWORDS = re.compile(r"(?i)AppData|HobbyProjects|pyenv|bluestacks|pagefile|\\\\Users|C:\\\\\\\\|C:/")
SECRET = re.compile(r"(sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|dev_[A-Za-z0-9]{8,}"
                    r"|api[_ -]?key\s*[:=]\s*\S+|Bearer\s+[A-Za-z0-9._-]{12,})",
                    re.IGNORECASE)
# Whatever escaping the log used, a drive letter followed by a separator is a
# path. This is the last pass so nothing like `C:\` survives.
LEFTOVER = re.compile(r"(?i)\b[a-z]:[\\/]")


SUBS = {"drive": 0, "home": 0, "msys": 0, "session_dir": 0, "user": 0,
        "secret": 0, "leakword": 0, "leftover": 0}


def scrub(text: str) -> str:
    for pat, key, rep in ((DRIVE, "drive", "<local-path>"),
                          (HOME, "home", "<local-path>"),
                          (MSYS, "msys", "<local-path>"),
                          (SESSION_DIR, "session_dir", "<session-dir>"),
                          (USER, "user", "<user>"),
                          (SECRET, "secret", "<redacted>"),
                          (LEAKWORDS, "leakword", "<local-path>"),
                          (LEFTOVER, "leftover", "<local-path>")):
        text, n = pat.subn(rep, text)
        SUBS[key] += n
    return text


def clip(text: str, n: int) -> str:
    """Scrub, then drop whole lines that still name the machine.

    A directory listing of the home folder is the worst offender: it is a
    tool output, but it says more about the person than any code does.
    """
    text = scrub(text)
    named = sum(1 for ln in text.splitlines() if "<user>" in ln or "<local-path>" in ln)
    if named > 3:
        return "<local directory listing omitted>"
    return text if len(text) <= n else text[:n].rstrip() + " …"


# ------------------------------------------------------------------ reading #
def load(session_file: str | None) -> list[dict]:
    """The newest Pi session log for this project unless one is named."""
    if session_file:
        path = Path(session_file)
    else:
        env = os.environ.get("PI_SESSION_FILE")
        if not env:
            raise SystemExit("PI_SESSION_FILE is not set; pass the jsonl path")
        path = Path(env)
    out = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        if d.get("type") == "message":
            out.append(d)
    return out


def curate(rows: list[dict]) -> list[dict]:
    msgs: list[dict] = []
    pending: dict[str, str] = {}     # toolCall id -> the tool_call block
    for d in rows:
        m = d["message"]
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, str):
            content = [{"type": "text", "text": content}]
        if role == "system":
            continue                                   # harness prompt, not work
        if role == "toolResult":
            for b in content:
                txt = b.get("content") or b.get("text") or ""
                if isinstance(txt, list):
                    txt = " ".join(x.get("text", "") for x in txt if isinstance(x, dict))
                for cid, blk in list(pending.items()):
                    blk["output"] = clip(str(txt), 420)
                    pending.pop(cid, None)
                    break
            continue
        blocks = []
        for b in content:
            t = b.get("type")
            if t == "thinking":
                txt = clip(b.get("thinking", ""), 320)
                if txt.strip():
                    blocks.append({"type": "text", "text": f"[thinking] {txt}"})
            elif t == "text":
                txt = clip(b.get("text", ""), 1400)
                if txt.strip():
                    blocks.append({"type": "text", "text": txt})
            elif t == "toolCall":
                blk = {"type": "tool_call",
                       "name": b.get("name", "?"),
                       "input": clip(json.dumps(b.get("arguments", {}),
                                               ensure_ascii=False), 320),
                       "output": ""}
                blocks.append(blk)
                pending[str(b.get("id"))] = blk
        if not blocks:
            continue
        msgs.append({"role": "user" if role == "user" else "assistant",
                     "content": blocks})
    return msgs


def leaks(blob: str) -> list[str]:
    """Snippets that still name the machine. Non-empty means: do not send."""
    return [blob[m.start() - 60:m.start() + 60]
            for m in list(LEAKWORDS.finditer(blob))[:8]]


def main() -> int:
    args = sys.argv[1:]
    check = "--check" in args
    named = [a for a in args if not a.startswith("-")]
    rows = load(named[0] if named else None)
    msgs = curate(rows)
    payload = {
        "messages": msgs,
        "metadata": {
            "tool_name": "pi",
            "session_id": os.environ.get("PI_SESSION_ID", ""),
            "total_messages": len(msgs),
        },
    }
    blob = json.dumps(payload, ensure_ascii=False, indent=1)
    hits = SECRET.findall(blob)
    bad = leaks(blob)
    print(f"messages: {len(msgs)} · payload {len(blob):,} chars · "
          f"scrub substitutions: { {k: v for k, v in SUBS.items() if v} } · "
          f"secret-shaped hits left: {len(hits)} · path leaks left: {len(bad)}")
    if hits or bad:
        for s in (hits[:5] + bad[:3]):
            print("  LEAK:", s.replace("\n", " ")[:140])
        print("REFUSING to write until these are reviewed")
        return 2
    if check:
        return 0
    out = Path("docs") / "devrelay-session.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print(f"wrote {out} ({len(blob):,} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
