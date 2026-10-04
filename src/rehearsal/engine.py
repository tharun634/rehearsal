"""llama.cpp adapter. One interface, three modes.

    mode = "server"  llama-server resident, OpenAI-compatible /v1/chat/completions
    mode = "cli"     llama-cli one-shot subprocess per call (nothing resident)
    mode = "mock"    deterministic canned responses, for tests and CI only

`server` is the fast path: the model stays resident across a whole session.
`cli` exists because the machine this was built on shares its GPU with another
local server; when that one is running there is no room for a second resident
model, so we pay the reload instead of the RAM.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import tomllib
from urllib.error import URLError
from urllib.request import Request, urlopen

ENGINE_TIMEOUT_S = 180


def load_engine_config(path: str) -> dict:
    with open(path, "rb") as fh:
        cfg = tomllib.load(fh)
    cfg.setdefault("mode", "server")
    cfg.setdefault("base_url", "http://127.0.0.1:8082")
    cfg.setdefault("model_name", "local")
    cfg.setdefault("n_predict", 320)
    cfg.setdefault("temperature", 0.6)
    cfg.setdefault("ngl", 99)
    cfg.setdefault("threads", 0)          # 0 = llama.cpp default
    cfg.setdefault("ctx", 4096)
    cfg.setdefault("gguf", "")
    cfg.setdefault("llama_cli", "")
    cfg.setdefault("llama_server", "")
    return cfg


class EngineError(RuntimeError):
    """Raised when llama.cpp is misconfigured or unreachable."""


class Engine:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.mode = cfg["mode"]
        # Every model call is timed and counted here: the post can only quote
        # numbers this object actually produced (docs/research/).
        self.usage_log: list[dict] = []

    # ---- public -------------------------------------------------------- #
    def complete(self, system: str, user: str, *, schema: dict | None = None,
                 temperature: float | None = None, max_tokens: int | None = None) -> str:
        temp = temperature if temperature is not None else self.cfg["temperature"]
        n = max_tokens if max_tokens is not None else self.cfg["n_predict"]
        t0 = time.time()
        if self.mode == "server":
            text, usage = _server(self.cfg, system, user, schema, temp, n)
        elif self.mode == "cli":
            text, usage = _cli(self.cfg, system, user, schema, temp, n)
        elif self.mode == "mock":
            text, usage = _mock(system, user, schema), {}
        else:
            raise EngineError(f"unknown engine mode {self.mode!r} in config/engine.toml")
        self.usage_log.append({"mode": self.mode, "seconds": round(time.time() - t0, 2),
                               **usage})
        return text

    def tokens(self) -> tuple[int, int]:
        """(prompt, completion) over every call this Engine made; cli mode cannot
        count tokens, so it reports 0 and the timings carry the evidence instead."""
        return (sum(c.get("prompt_tokens") or 0 for c in self.usage_log),
                sum(c.get("completion_tokens") or 0 for c in self.usage_log))


def _render_turns(turns: list[tuple[str, str]]) -> str:
    """Flatten a transcript for one-shot mode (llama-cli has no chat history)."""
    lines = []
    for who, text in turns:
        lines.append(f"{who}: {text}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# server mode
# --------------------------------------------------------------------------- #
def _server(cfg: dict, system: str, user: str, schema: dict | None, temp: float, n: int) -> tuple[str, dict]:
    body = {
        "model": cfg["model_name"],
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temp,
        "max_tokens": n,
        "n_predict": n,
        "stream": False,
    }
    if schema:
        # llama.cpp compiles this into a GBNF grammar: the model cannot emit
        # anything that does not parse. That is what makes the coach payload
        # safe to hand to sqlite without a repair loop.
        body["response_format"] = {"type": "json_schema", "json_schema": {"schema": schema}}
    url = cfg["base_url"].rstrip("/") + "/v1/chat/completions"
    req = Request(url, data=json.dumps(body).encode("utf-8"),
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=ENGINE_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (URLError, OSError) as exc:
        raise EngineError(
            f"llama-server not reachable at {url} ({exc}). "
            f"Start it, or set mode = \"cli\" in config/engine.toml."
        ) from exc
    except json.JSONDecodeError as exc:
        raise EngineError(f"llama-server returned a non-JSON body: {data!r}") from exc
    try:
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
    except (KeyError, IndexError, TypeError) as exc:
        raise EngineError(f"unexpected chat-completion shape: {data!r}") from exc
    return content, {"prompt_tokens": usage.get("prompt_tokens"),
                     "completion_tokens": usage.get("completion_tokens")}


# --------------------------------------------------------------------------- #
# cli mode — one model load per call, nothing resident
# --------------------------------------------------------------------------- #
def _cli_schema_hint(schema: dict) -> str:
    """cli mode cannot compile a GBNF grammar (see _cli), so the schema becomes a
    shape the model fills in. A skeleton reads as "answer in this shape"; the raw
    JSON Schema reads as "repeat this text", which is what Gemma did."""
    def sample(node: dict) -> str:
        t = node.get("type", "string")
        if t == "object":
            inner = node.get("properties", {})
            keys = node.get("required") or list(inner)
            return "{" + ", ".join(
                f'"{k}": {sample(inner[k])}' for k in keys if k in inner) + "}"
        if t == "array":
            return "[" + sample(node.get("items", {"type": "string"})) + "]"
        return {"boolean": "true", "integer": "1", "number": "1.0"}.get(t, '"text"')
    props = schema.get("properties", {})
    keys = schema.get("required") or list(props)
    body = ", ".join(f'"{k}": {sample(props[k])}' for k in keys if k in props)
    return "{" + body + "}"


def _cli(cfg: dict, system: str, user: str, schema: dict | None, temp: float, n: int) -> tuple[str, dict]:
    exe = cfg.get("llama_cli")
    if not exe:
        raise EngineError("cli mode needs llama_cli = \"...\" in config/engine.toml")
    argv = [exe, "-m", cfg["gguf"], "-sys", system, "-p", user,
            "-n", str(n), "--temp", str(temp), "-ngl", str(cfg["ngl"]),
            "-c", str(cfg["ctx"]), "--single-turn", "--no-display-prompt",
            "--no-log-prefix", "--color", "off"]
    if cfg["threads"]:
        argv += ["-t", str(cfg["threads"])]
    prompt = user
    if schema:
        # cli mode CANNOT use llama.cpp's grammar sampler with Gemma: -j dies with
        # "Failed to initialize samplers: Unexpected empty grammar stack after
        # accepting piece: <start_of_turn>" on build b11379 (see DECISIONS.md).
        # So the shape is in the prompt here, and parse_json_loose is the net.
        prompt += (
            "\n\nReply with exactly one JSON object and no prose, no code fences, "
            "in this shape (your own values, not these placeholders): "
            + _cli_schema_hint(schema)
        )
        argv[argv.index(user) if user in argv else 5] = prompt
    # -o holds the echoed prompt plus the completion, and nothing else: no ASCII
    # banner, no loader chatter. The scratch file is a local copy of the friend's
    # turn and is unlinked below.
    fd, out_path = tempfile.mkstemp(prefix="rehearsal-cli-", suffix=".txt")
    os.close(fd)
    argv += ["-o", out_path]
    try:
        out = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=ENGINE_TIMEOUT_S * 2)
        try:
            raw = open(out_path, encoding="utf-8", errors="replace").read()
        except OSError:
            raw = ""
    except FileNotFoundError:
        raise EngineError(f"llama-cli not found at {exe!r}. Fix llama_cli in config/engine.toml.")
    except subprocess.TimeoutExpired:
        raise EngineError("llama-cli timed out; try a smaller -ngl, a smaller model, or server mode.")
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass
    if out.returncode != 0:
        raise EngineError(f"llama-cli exit {out.returncode}: {out.stderr[-400:]!r}")
    # llama-cli echoes the prompt into the output file; cut at the last copy of it
    # so the completion alone reaches the parser.
    i = raw.rfind(prompt)
    text = raw[i + len(prompt):] if i >= 0 else raw
    text = text.strip()
    if text.lower().startswith("assistant:"):
        text = text[len("assistant:"):].strip()
    if not text:
        raise EngineError("llama-cli wrote nothing after the prompt; "
                          f"stderr tail: {out.stderr[-300:]!r}")
    # llama-cli prints its own speed line; that is the only token evidence cli
    # mode gives, so it goes in the usage log rather than being thrown away.
    m = re.search(r"Prompt: ([\d.]+) t/s \| Generation: ([\d.]+) t/s",
                  out.stdout + out.stderr)
    usage = {"prompt_tps": float(m.group(1)) if m else None,
             "gen_tps": float(m.group(2)) if m else None,
             "n_predict": n}
    return text, usage


# --------------------------------------------------------------------------- #
# mock mode — canned, deterministic, never used for a real session
# --------------------------------------------------------------------------- #
def _mock(system: str, user: str, schema: dict | None) -> str:
    if schema is PARTNER_SCHEMA:
        return json.dumps({
            "line": "Ah, good morning! Welcome to Café Aoi. What would you like today?",
            "tasks_done": ["greet"], "goal_met": False, "pressure": "casual",
        })
    if schema is COACH_SCHEMA:
        return json.dumps({
            "understood": True,
            "errors": [{"said": "sato", "fix": "satoh",
                        "why": "Final -s in a loanword needs the long vowel: satoo/satoh.",
                        "kind": "pronunciation"}],
            "better": "Ahara, sumisu no ogi, please.",
            "nudge": "You ordered fine — the barista heard you.",
            "level": 2,
        })
    if schema:
        # any other schema: build the smallest object that validates, so `doctor`
        # can prove the plumbing without pretending the model is good.
        return json.dumps(_mock_object(schema), ensure_ascii=False)
    return "mock engine: canned reply"


def _mock_object(schema: dict) -> dict:
    out = {}
    for key, spec in schema.get("properties", {}).items():
        out[key] = _mock_value(spec)
    return out


def _mock_value(spec: dict):
    t = spec.get("type")
    if "enum" in spec:
        return spec["enum"][0]
    if t == "string":
        return "mock"
    if t == "boolean":
        return True
    if t == "integer":
        return spec.get("minimum", 1)
    if t == "array":
        return [_mock_value(spec["items"])] if "items" in spec else []
    if t == "object":
        return _mock_object(spec)
    return "mock"


PARTNER_SCHEMA = {
    "type": "object",
    "properties": {
        "line": {"type": "string"},
        "tasks_done": {"type": "array", "items": {"type": "string"}},
        "goal_met": {"type": "boolean"},
        "pressure": {"type": "string"},
    },
    "required": ["line", "tasks_done", "goal_met"],
    "additionalProperties": False,
}

COACH_SCHEMA = {
    "type": "object",
    "properties": {
        "understood": {"type": "boolean"},
        "errors": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "said": {"type": "string"},
                "fix": {"type": "string"},
                "why": {"type": "string"},
                "kind": {"type": "string",
                         "enum": ["grammar", "particle", "pronunciation", "register",
                                  "word_order", "vocabulary", "comprehension"]},
            },
            "required": ["said", "fix", "why", "kind"],
            "additionalProperties": False,
        }},
        "better": {"type": "string"},
        "nudge": {"type": "string"},
        "level": {"type": "integer", "minimum": 1, "maximum": 5},
    },
    "required": ["understood", "errors", "better", "nudge"],
    "additionalProperties": False,
}


def parse_json_loose(text: str, schema: dict) -> dict:
    """Grammar-constrained calls never hit the fallback; the fallback is for cli
    mode and older llama.cpp builds that ignore response_format."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise EngineError(
        "model did not return JSON. In server mode this means response_format was "
        "ignored — check the llama.cpp version, or run `rehearsal doctor`. "
        f"raw[:240] = {text[:240]!r}"
    )
