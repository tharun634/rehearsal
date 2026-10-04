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


def _call(engine, system, user, schema, temp, n, echo):
    """One model call, one retry at temp 0.

    A 4B model occasionally ignores the shape on a long turn (measured: the
    coach call on turn 2 of the cafe scene, 320 tokens, prose). Asking again
    cold is cheaper than losing the turn; a second failure ends the session
    with whatever was already recorded, because half a session is still
    evidence and a crash is not.
    """
    try:
        return parse_json_loose(engine.complete(system, user, schema=schema,
                                                temperature=temp, max_tokens=n), schema)
    except EngineError as first:
        if echo:
            print(f"  engine: {first}")
        try:
            return parse_json_loose(engine.complete(system, user, schema=schema,
                                                    temperature=0.0, max_tokens=n), schema)
        except EngineError as second:
            if echo:
                print(f"  engine: {second}")
            return None


def practice(engine, learner: dict, scenario: dict, con, *,
             max_turns: int = 12, echo: bool = True,
             script: list[str] | None = None) -> dict:
    sys_partner = partner_system(scenario, learner, watchlist(con))
    sys_coach = coach_system(learner, watchlist(con))
    transcript: list[tuple[str, str]] = []
    log: list[dict] = []
    done: set[str] = set()
    goal_met = False
    corrections = 0
    t0 = time.time()
    turns = 0

    for i in range(max_turns):
        # ---- partner speaks ------------------------------------------ #
        pu = _partner_user(scenario, transcript, done)
        p = _call(engine, sys_partner, pu, PARTNER_SCHEMA, 0.8, 160, echo)
        if p is None:
            break
        line = p.get("line", "").strip()
        if not line:
            break
        transcript.append(("Partner", line))
        newly = [t for t in p.get("tasks_done", []) if t not in done]
        done.update(newly)
        if echo:
            print(f"\n{scenario['partner_name']}: {line}")
            if newly:
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
        report = _call(engine, sys_coach, coach_user(scenario, transcript, mine),
                       COACH_SCHEMA, 0.2, 512, echo)
        if report is None:
            # the learner's line still belongs in memory; the coach's notes do not exist
            report = {"understood": False, "errors": [], "better": "", "nudge": ""}
            if echo:
                print("  (coach call failed — the line is saved, nothing was graded)")
        report["errors"] = [e for e in report.get("errors", []) if e.get("said")]
        # the 4B model re-states the same correction twice sometimes; the deck
        # would carry the duplicate into sqlite and the SRS would show it twice
        seen_spans: set[str] = set()
        report["errors"] = [e for e in report["errors"]
                            if not seen_spans.add(e["said"].strip().lower())]
        corrections += len(report["errors"])
        record_turn(con, scenario["id"], mine, line, report)
        log.append({"partner": line, "you": mine, "coach": report,
                    "tasks_done": newly})
        turns += 1
        if echo:
            _print_report(report)

    secs = time.time() - t0
    pt, ct = engine.tokens()
    record_session(con, scenario["id"], turns, corrections, goal_met, secs, ct)
    return {"turns": turns, "corrections": corrections, "goal_met": goal_met,
            "seconds": round(secs, 1), "tasks_done": sorted(done),
            "tokens": [pt, ct], "transcript": transcript, "log": log}


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
