"""Long-term memory for one learner: sqlite, on disk, never uploaded.

This is the whole "for a friend" argument. The partner prompt reads a watch list
built from THIS person's past turns, so the hundredth session is not the first
session. A closed API could do the same thing only by shipping their turns —
who they talk about, where they work, what they are doing — to someone's server.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB = "data/learner.sqlite3"

KIND_LABEL = {
    "grammar": "grammar",
    "particle": "particles",
    "pronunciation": "sound / spelling",
    "register": "politeness / register",
    "word_order": "word order",
    "vocabulary": "word choice",
    "comprehension": "being understood",
}


def connect(db: str = DB):
    """One handle per db path. Windows raises 'database is locked' when two
    sqlite handles to the same file are open at once, and every command here
    opens the file, so the handles are cached instead of stacked."""
    if db in _HANDLES:
        return _HANDLES[db]
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    for table in (
        """CREATE TABLE turns(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             ts TEXT, scenario TEXT, learner_text TEXT, partner_line TEXT,
             understood INTEGER, level INTEGER, errors_json TEXT, better TEXT)""",
        """CREATE TABLE cards(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             kind TEXT, said TEXT, fix TEXT, why TEXT,
             due TEXT, reps INTEGER, lapses INTEGER, ease REAL, interval REAL,
             created TEXT, scenario TEXT)""",
        """CREATE TABLE sessions(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             ts TEXT, scenario TEXT, turns INTEGER, corrections INTEGER,
             goal_met INTEGER, seconds REAL, tok INTEGER)""",
    ):
        try:
            con.execute(table)
        except sqlite3.OperationalError:
            pass  # already created
    _HANDLES[db] = con
    return con


_HANDLES: dict[str, "sqlite3.Connection"] = {}


def record_turn(con, scenario: str, learner_text: str, partner_line: str,
                report: dict) -> int:
    ts = datetime.now().isoformat(timespec="seconds")
    cur = con.execute(
        "INSERT INTO turns(ts,scenario,learner_text,partner_line,understood,level,"
        "errors_json,better) VALUES(?,?,?,?,?,?,?,?)",
        (ts, scenario, learner_text, partner_line,
         int(bool(report.get("understood", False))),
         int(report.get("level", 2) or 2),
         json.dumps(report.get("errors", []), ensure_ascii=False),
         report.get("better", "")),
    )
    for err in report.get("errors", [])[:3]:
        kind = err.get("kind", "grammar")
        if not err.get("said") or not err.get("fix"):
            continue
        con.execute(
            "INSERT INTO cards(kind,said,fix,why,due,reps,lapses,ease,interval,"
            "created,scenario) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (kind, err["said"], err["fix"], err.get("why", ""),
             ts, 0, 0, 2.5, 0.0, ts, scenario),
        )
    return int(cur.lastrowid)


def record_session(con, scenario: str, turns: int, corrections: int,
                   goal_met: bool, seconds: float, tok: int) -> None:
    con.execute(
        "INSERT INTO sessions(ts,scenario,turns,corrections,goal_met,seconds,tok) "
        "VALUES(?,?,?,?,?,?,?)",
        (datetime.now().isoformat(timespec="seconds"), scenario, turns,
         corrections, int(goal_met), round(seconds, 1), tok),
    )


# --------------------------------------------------------------------------- #
def watchlist(con, limit: int = 8) -> list[str]:
    """Recurring weak spots, phrased as instructions the partner can act on."""
    cur = con.execute(
        "SELECT kind, COUNT(*) FROM cards GROUP BY kind ORDER BY COUNT(*) DESC"
    )
    out = []
    for kind, n in cur.fetchall():
        label = KIND_LABEL.get(kind, kind)
        sample = con.execute(
            "SELECT said, fix FROM cards WHERE kind = ? ORDER BY id DESC", (kind,)
        ).fetchone()
        if sample:
            out.append(f"{label} ({n}x): they said {sample[0]!r}, meant {sample[1]!r}")
        else:
            out.append(f"{label} ({n}x)")
        if len(out) >= limit:
            break
    return out


def stats(con) -> dict:
    turns = con.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    cards = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    sess = con.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    understood = con.execute("SELECT SUM(understood) FROM turns").fetchone()[0] or 0
    per_kind = dict(con.execute(
        "SELECT kind, COUNT(*) FROM cards GROUP BY kind ORDER BY COUNT(*) DESC"
    ).fetchall())
    return {"turns": turns, "cards": cards, "sessions": sess,
            "understood_rate": (understood / turns) if turns else 0.0,
            "kinds": per_kind}


def due_cards(con, limit: int = 20) -> list[tuple]:
    now = datetime.now().isoformat(timespec="seconds")
    rows = con.execute(
        "SELECT id,kind,said,fix,why,due,reps,lapses,ease,interval FROM cards "
        "ORDER BY due").fetchall()
    return [r for r in rows if r[5] <= now][:limit]


def grade(con, card_id: int, rating: int) -> None:
    """SM-2 lite. rating 0 again, 1 hard, 2 good, 3 easy."""
    reps, lapses, ease, interval = con.execute(
        "SELECT reps,lapses,ease,interval FROM cards WHERE id = ?", (card_id,)
    ).fetchone()
    q = (0.0, 0.7, 1.5, 2.5)[rating]
    ease = max(1.3, ease - 0.1 + q * 0.15)
    if rating == 0:
        lapses += 1
        interval = 0.0
    else:
        interval = 1.0 if reps == 0 else max(1.0, interval * ease)
        if lapses:
            interval = min(interval, 0.5)
    due = datetime.now() + timedelta(days=max(0.02, interval))
    con.execute(
        "UPDATE cards SET reps=?,lapses=?,ease=?,interval=?,due=? WHERE id=?",
        (reps + 1, lapses, round(ease, 3), round(interval, 3),
         due.isoformat(timespec="seconds"), card_id),
    )
