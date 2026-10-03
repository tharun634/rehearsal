"""The thing you actually hand over: a printable sheet of THIS person's weak spots.

Stdlib HTML, no CSS framework, prints on A4 from any browser. A hosted app was
the thing we were asked not to build; a sheet you can tape inside a fridge is
the thing a friend can use.
"""
from __future__ import annotations

import html
from datetime import datetime

from .memory import connect, stats, watchlist
from .prompts import load_scenarios


def build_html(learner: dict) -> str:
    con = connect()
    st = stats(con)
    kinds = st["kinds"]
    rows = con.execute(
        "SELECT kind, said, fix, why FROM cards ORDER BY id DESC").fetchall()
    seen, blocks = set(), []
    for kind, said, fix, why in rows:
        key = (kind, said)
        if key in seen:
            continue
        seen.add(key)
        blocks.append(
            f"<li><b>{html.escape(said)}</b> → <b>{html.escape(fix)}</b>"
            f"<br><span class='why'>{html.escape(why or '')}</span></li>"
        )
        if len(blocks) >= 24:
            break
    watch = "".join(f"<li>{html.escape(w)}</li>" for w in watchlist(con, limit=10))
    kind_rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{n}</td></tr>" for k, n in kinds.items()
    )
    return f"""<!doctype html>
<meta charset="utf-8">
<title>{html.escape(learner['name'])} — rehearsal sheet</title>
<style>
 body{{font:15px/1.4 Georgia,serif;margin:14mm;}}
 h1{{font-size:20px;}} .why{{color:#555;font-size:12px;}}
 table{{border-collapse:collapse;}} td{{border:1px solid #bbb;padding:3px 6px;}}
 @media print{{ .pagebreak{{page-break-before:always;}} }}
</style>
<h1>{html.escape(learner['name'])} — the {st['cards']} things I keep getting wrong</h1>
<p><i>Generated {datetime.now():%Y-%m-%d} by rehearsal, from {st['turns']} turns
across {st['sessions']} sessions. Nothing here left this machine.</i></p>
<h2>Where I slip most</h2>
<table>{kind_rows or '<tr><td>no data</td><td>—</td></tr>'}</table>
<h2>Watch list (what the partner keeps setting up)</h2>
<ul>{watch or '<li>first session — nothing yet</li>'}</ul>
<h2>Fixes, newest first</h2>
<ul>{''.join(blocks) or '<li>no corrections yet</li>'}</ul>
<h2>Scenes to practise next</h2>
<ul>{''.join(f'<li>{html.escape(s["title"])} — {html.escape(s["goal"])}</li>'
              for s in load_scenarios().values())}</ul>
"""


def report(out: str, learner: dict) -> str:
    doc = build_html(learner)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return out
