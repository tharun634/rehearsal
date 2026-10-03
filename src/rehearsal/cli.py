"""Command line. Run as:  python -m rehearsal.cli <verb>

Verbs:
  doctor      is llama.cpp reachable, and can it emit schema-valid JSON?
  scenarios   list the scenes
  practice    run a session with the partner + coach
  review      drill this learner's own cards
  report      write the printable hand-over sheet
  stats       what the memory holds
  profile     set the friend, the language, the level
"""
from __future__ import annotations

import argparse
import io
import sys

from .engine import load_engine_config, Engine, EngineError, parse_json_loose
from .memory import connect, stats
from .prompts import load_learner, load_scenarios
from .session import practice
from .srs import review
from .report import report

CONFIG_ENGINE = "config/engine.toml"
CONFIG_LEARNER = "config/learner.toml"


def _utf8() -> None:
    """Windows consoles default to cp1252; Japanese turns would crash on print."""
    from .console import utf8_console
    utf8_console()


def cmd_doctor(engine_mode: str | None) -> int:
    cfg = load_engine_config(CONFIG_ENGINE)
    if engine_mode:
        cfg["mode"] = engine_mode
    print(f"engine mode: {cfg['mode']}")
    eng = Engine(cfg)
    try:
        raw = eng.complete(
            "Reply with JSON only.",
            'Say the word "ok".',
            schema={"type": "object",
                    "properties": {"ok": {"type": "boolean"}},
                    "required": ["ok"], "additionalProperties": False},
            temperature=0.0, max_tokens=32,
        )
    except EngineError as exc:
        print(f"ENGINE: {exc}")
        return 1
    try:
        parsed = parse_json_loose(raw, {"type": "object"})
    except EngineError as exc:
        print(f"MODEL JSON: {exc}")
        return 2
    print(f"raw: {raw[:120]!r}")
    print(f"parsed: {parsed}")
    return 0


def cmd_practice(scenario_id: str, turns: int, engine_mode: str | None) -> int:
    learner = load_learner(CONFIG_LEARNER)
    scenarios = load_scenarios()
    if scenario_id not in scenarios:
        print(f"unknown scene {scenario_id!r}: try `scenarios`")
        return 1
    cfg = load_engine_config(CONFIG_ENGINE)
    if engine_mode:
        cfg["mode"] = engine_mode
    con = connect()
    try:
        result = practice(Engine(cfg), learner, scenarios[scenario_id], con,
                          max_turns=turns)
    except EngineError as exc:
        print(f"ENGINE: {exc}")
        return 1
    print(f"\nsession: {result['turns']} turns, {result['corrections']} corrections, "
          f"scene {'cleared' if result['goal_met'] else 'not cleared'} "
          f"in {result['seconds']}s")
    return 0


def cmd_review(n: int, engine_mode: str | None) -> int:
    print(review(connect(), n=n))
    return 0


def cmd_report(out: str) -> int:
    print(report(out, load_learner(CONFIG_LEARNER)))
    return 0


def cmd_stats() -> int:
    print(stats(connect()))
    return 0


def cmd_scenarios() -> int:
    for s in load_scenarios().values():
        print(f"  {s['id']:16} {s['title']}")
    return 0


def cmd_profile(name: str, language: str, level: str, l1: str) -> int:
    import tomllib
    from pathlib import Path
    with open(CONFIG_LEARNER, "rb") as fh:
        cur = tomllib.load(fh)
    cur.update({k: v for k, v in
                (("name", name), ("language", language), ("level", level), ("l1", l1))
                if v})
    body = "\n".join(f"{k} = {_toml_value(v)}" for k, v in cur.items())
    Path(CONFIG_LEARNER).write_text(
        "# the friend. edit this file, or: rehearsal profile --name ...\n" + body + "\n",
        encoding="utf-8")
    print(f"wrote {CONFIG_LEARNER}")
    return 0


def _toml_value(v) -> str:
    import json
    return json.dumps(v, ensure_ascii=False)


def main(argv: list[str]) -> int:
    _utf8()
    p = argparse.ArgumentParser(prog="rehearsal")
    sub = p.add_subparsers(dest="verb", required=True)
    for name in ("scenarios", "stats"):
        sub.add_parser(name)
    pr = sub.add_parser("practice")
    pr.add_argument("--scenario", required=True)
    pr.add_argument("--turns", type=int, default=12)
    pr.add_argument("--engine")
    rv = sub.add_parser("review")
    rv.add_argument("--n", type=int, default=10)
    rp = sub.add_parser("report")
    rp.add_argument("--out", default="docs/handout.html")
    pf = sub.add_parser("profile")
    for flag in ("--name", "--language", "--level", "--l1"):
        pf.add_argument(flag, default=None)
    d = sub.add_parser("doctor")
    d.add_argument("--engine")

    args = p.parse_args(argv)
    if args.verb == "doctor":
        return cmd_doctor(getattr(args, "engine", None))
    if args.verb == "scenarios":
        return cmd_scenarios()
    if args.verb == "stats":
        return cmd_stats()
    if args.verb == "practice":
        return cmd_practice(args.scenario, args.turns, args.engine)
    if args.verb == "review":
        return cmd_review(args.n, None)
    if args.verb == "report":
        return cmd_report(args.out)
    if args.verb == "profile":
        return cmd_profile(args.name, args.language, args.level, args.l1)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
