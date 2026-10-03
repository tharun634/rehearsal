"""Drilling the learner's own sentences. Not a lesson deck — their mistakes.

The front of every card is something THIS person actually typed. That is the
part a downloaded deck cannot give a friend.
"""
from __future__ import annotations

import difflib

from .memory import connect, due_cards, grade

MATCH = 0.86  # SequenceMatcher ratio; tuned at M4, see docs/research/


def review(con, n: int = 10, *, auto: list[str] | None = None) -> dict:
    cards = due_cards(con, limit=n)
    if not cards:
        print("nothing due — the deck is empty or everything is scheduled out.")
        return {"seen": 0, "right": 0}
    right = 0
    for i, (cid, kind, said, fix, why, *_ ) in enumerate(cards):
        print(f"\n[{kind}] put it right:")
        print(f"  they had said: {said}")
        if auto is not None:
            answer = auto[i] if i < len(auto) else ""
        else:
            try:
                answer = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
        if not answer:
            break
        ratio = difflib.SequenceMatcher(None, answer, fix).ratio()
        if ratio >= MATCH:
            right += 1
            grade(con, cid, 2 if ratio < 0.97 else 3)
            print(f"  ✓ {ratio:.0%}")
        else:
            grade(con, cid, 0)
            print(f"  ✗ {ratio:.0%} — wanted: {fix}")
            print(f"    {why}")
    return {"seen": len(cards), "right": right}
