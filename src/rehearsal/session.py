"""The practice loop: partner turn -> learner turn -> coach report -> memory.

Two model calls per turn. That is the honest cost of the design: the partner
must not see the coach's notes (a partner that sees corrections stops being a
person), so it gets its own call with its own prompt. Measured numbers live in
docs/research/.
"""
from __future__ import annotations

import json
import time

from .engine import PARTNER_SCHEMA, COACH_SCHEMA, EngineError, parse_json_loose
from .memory import connect, record_turn, record_session, watchlist
from .prompts import partner_system, coach_system, coach_user


def practice(engine, learner: dict, scenario: dict, con, *,
             max_turns: int = 12, echo: bool = True,
             script: list[str] | None = None) -> dict:
    sys_partner = partner_system(scenario, learner, watchlist(con))
    sys_coach = coach_system(learner, watchlist(con))
    transcript: list[tuple[str, str]] = []
    done: set[str] = set()
    goal_met = False
    corrections = 0
    t0 = time.time()
    turns = 0

    for i in range(max_turns):
        # ---- partner speaks ------------------------------------------ #
        pu = _partner_user(scenario, transcript, done)
        praw = engine.complete(sys_partner, pu, schema=PARTNER_SCHEMA,
                               temperature=0.8, max_tokens=160)
        p = parse_json_loose(praw, PARTNER_SCHEMA)
        line = p.get("line", "").strip()
        if not line:
            break
        transcript.append(("Partner", line))
        if echo:
            print(f"\n{scenario['partner_name']}: {line}")
            newly = [t for t in p.get("tasks_done", []) if t not in done]
            done.update(newly)
            if newly and echo:
                print(f"  · scene: {', '.join(newly)}")
        if p.get("goal_met"):
            goal_met = True

        # ---- learner speaks ------------------------------------------ #
        if script is not None:               # scripted: tests and the demo recording
            mine = script[i] if i < len(script) else ""
        else:
            try:
                mine = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                mine = ""
        if not mine:
            break
        transcript.append(("You", mine))

        # ---- coach reports ------------------------------------------- #
        craw = engine.complete(sys_coach, coach_user(scenario, transcript, mine),
                               schema=COACH_SCHEMA, temperature=0.2, max_tokens=320)
        report = parse_json_loose(craw, COACH_SCHEMA)
        report["errors"] = [e for e in report.get("errors", []) if e.get("said")]
        corrections += len(report["errors"])
        record_turn(con, scenario["id"], mine, line, report)
        turns += 1
        if echo:
            _print_report(report)

    secs = time.time() - t0
    record_session(con, scenario["id"], turns, corrections, goal_met, secs, 0)
    return {"turns": turns, "corrections": corrections, "goal_met": goal_met,
            "seconds": round(secs, 1), "tasks_done": sorted(done)}


def _partner_user(scenario: dict, transcript: list[tuple[str, str]],
                  done: set[str]) -> str:
    body = "\n".join(f"{who}: {text}" for who, text in transcript[-10:])
    left = [t["id"] for t in scenario["tasks"] if t["id"] not in done]
    return (f"Table so far:\n{body or '(empty — open the scene with your first line)'}\n\n"
            f"Still outstanding: {', '.join(left) or '(none — close the scene)'}\n"
            "Your next line as the partner.")


def _print_report(report: dict) -> None:
    if report.get("understood"):
        print("  ✓ they got across")
    else:
        print("  ? they did not get across")
    for e in report["errors"]:
        print(f"  - {e['said']} → {e['fix']}  [{e['kind']}]")
        print(f"    {e['why']}")
    if report.get("better"):
        print(f"  say instead: {report['better']}")
    if report.get("nudge"):
        print(f"  (coach nudge, not spoken to the partner: {report['nudge']})")
