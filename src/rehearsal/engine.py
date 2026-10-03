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
import subprocess
import sys
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

    # ---- public -------------------------------------------------------- #
    def complete(self, system: str, user: str, *, schema: dict | None = None,
                 temperature: float | None = None, max_tokens: int | None = None) -> str:
        temp = temperature if temperature is not None else self.cfg["temperature"]
        n = max_tokens if max_tokens is not None else self.cfg["n_predict"]
        if self.mode == "server":
            return _server(self.cfg, system, user, schema, temp, n)
        if self.mode == "cli":
            return _cli(self.cfg, system, user, schema, temp, n)
        if self.mode == "mock":
            return _mock(system, user, schema)
        raise EngineError(f"unknown engine mode {self.mode!r} in config/engine.toml")


def _render_turns(turns: list[tuple[str, str]]) -> str:
    """Flatten a transcript for one-shot mode (llama-cli has no chat history)."""
    lines = []
    for who, text in turns:
        lines.append(f"{who}: {text}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# server mode
# --------------------------------------------------------------------------- #
def _server(cfg: dict, system: str, user: str, schema: dict | None, temp: float, n: int) -> str:
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
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise EngineError(f"unexpected chat-completion shape: {data!r}") from exc


# --------------------------------------------------------------------------- #
# cli mode — one model load per call, nothing resident
# --------------------------------------------------------------------------- #
def _cli(cfg: dict, system: str, user: str, schema: dict | None, temp: float, n: int) -> str:
    exe = cfg.get("llama_cli") or cfg.get("llama_server", "").replace("server", "cli")
    if not exe:
        raise EngineError("cli mode needs llama_cli = \"...\" in config/engine.toml")
    prompt = user
    if schema:
        prompt += (
            "\n\nRespond with a single JSON object and nothing else. It must match exactly:\n"
            + json.dumps(schema, ensure_ascii=False)
        )
    argv = [exe, "-m", cfg["gguf"], "-p", prompt, "--sys", system,
            "-n", str(n), "--temp", str(temp), "-ngl", str(cfg["ngl"]),
            "-c", str(cfg["ctx"]), "--no-echo", "--std"]
    if cfg["threads"]:
        argv += ["-t", str(cfg["threads"])]
    try:
        out = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                             errors="replace", timeout=ENGINE_TIMEOUT_S * 2)
    except FileNotFoundError:
        raise EngineError(f"llama-cli not found at {exe!r}. Fix llama_cli in config/engine.toml.")
    except subprocess.TimeoutExpired:
        raise EngineError("llama-cli timed out; try a smaller -ngl or a smaller model.")
    if out.returncode != 0:
        raise EngineError(f"llama-cli exit {out.returncode}: {out.stderr[-400:]!r}")
    return _clean_cli_stdout(out.stdout)


def _clean_cli_stdout(raw: str) -> str:
    """llama-cli mixes loader chatter into stdout; keep the completion only."""
    keep = []
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith(("llama_", "load_", "main:", "init_", "print_", "slot ", "Llama p",
                         "n_ctx", "GGUF", "get_", "set_", "ctx ", "encode_", "decode_")):
            continue
        keep.append(line)
    text = "\n".join(keep).strip()
    return text


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
        "ignored — check the llama.cpp version, or run `rehearsal doctor`."
    )
