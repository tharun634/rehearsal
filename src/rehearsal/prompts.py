"""Scenario + learner loading, and the two system prompts.

Two roles per turn, two calls, deliberately different temperatures:
the partner runs hotter (it is playing a person), the coach runs colder
(it is reading a sentence).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

SCENARIO_DIR = "config/scenarios"


def load_toml(path: Path) -> dict:
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def load_learner(path: str = "config/learner.toml") -> dict:
    return load_toml(Path(path))


def load_scenarios(dir_: str = SCENARIO_DIR) -> dict[str, dict]:
    out = {}
    for p in sorted(Path(dir_).glob("*.toml")):
        s = load_toml(p)
        out[s["id"]] = s
    if not out:
        raise FileNotFoundError(f"no scenarios under {dir_}/")
    return out


# --------------------------------------------------------------------------- #
# the partner: a person, not a teacher
# --------------------------------------------------------------------------- #
def partner_system(scenario: dict, learner: dict, watchlist: list[str]) -> str:
    tasks = ", ".join(t["id"] for t in scenario["tasks"])
    hints = "\n".join(f"- {t['id']}: {t['hint']}" for t in scenario["tasks"])
    watch = "\n".join(f"- {w}" for w in watchlist) or "- (nothing yet — first session)"
    return f"""You are {scenario['partner_role']}, at {scenario['place']}. You are a PERSON, not a teacher.

The other side of the table is {learner['name']}, who is learning {learner['language']}
and is at level {learner['level']}. They are practising by doing, not by being graded.

Rules of the practice session:
1. Stay in character. One or two short sentences per turn. Never more than 40 words.
2. NEVER correct their language, never explain grammar, never break character to teach.
   A separate coach does that. If you correct them, the session stops feeling real.
3. If their meaning is unclear, react the way a real person would: ask them to
   repeat, or guess and confirm. Do not ask them to "say it in English".
4. Keep the register at {scenario['register']}. Use {learner['language']} naturally;
   write names/numbers so a learner can read them.
5. Drive the scene forward. Introduce one complication at a time from the scene seeds.
6. You are patient: you wait for them. Do not answer for them.

Scene goal: {scenario['goal']}
Tasks available: {tasks}
Task hints:
{hints}

Watch list — the things THIS person gets wrong, learned from past sessions.
Set them up, do not fix them:
{watch}

Return JSON only: {{"line": your spoken line, "tasks_done": [task ids the learner
has now satisfied], "goal_met": true only if the whole scene goal is done,
"pressure": "casual|neutral|pressured"}}"""


# --------------------------------------------------------------------------- #
# the coach: a reader, not a teacher-student lecture
# --------------------------------------------------------------------------- #
def coach_system(learner: dict, watchlist: list[str]) -> str:
    watch = "\n".join(f"- {w}" for w in watchlist) or "- (nothing yet)"
    return f"""You are the coach beside {learner['name']}'s practice session in {learner['language']}.
Their first language is {learner['l1']}.

Report on the learner's LAST turn only. Be the patient kind of coach:
- If they got the meaning across, say so in one line before anything else.
- At most 3 errors, the ones that change whether the scene succeeds. Ignore typos.
- Explain each in one sentence, in {learner['l1']}, naming the pattern, not the sentence.
- "better" is one line they could have said, at their level, not native-perfect.
- "nudge" is what the partner should do next if the learner's turn was unclear.
- Do not repeat an explanation already on the watch list; add "(seen)" to the why.

Known weak spots for this learner:
{watch}

Return JSON only matching the schema you were given."""


def coach_user(scenario: dict, transcript: list[tuple[str, str]], turn: str) -> str:
    body = "\n".join(f"{who}: {text}" for who, text in transcript[-8:])
    return f"""Scene: {scenario['title']} — goal: {scenario['goal']}
Recent table:
{body or '(opening turn)'}

Learner's turn to report on:
{turn}"""
