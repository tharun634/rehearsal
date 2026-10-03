"""End-to-end pipeline test with the mock engine: turns in, memory out.

Run from the repo root:  python -m unittest tests.test_pipeline
The mock engine is the only place this repo runs without llama.cpp; it is
labelled in engine.py and `doctor --engine mock` is how you see that.
"""
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rehearsal.engine import Engine, load_engine_config, parse_json_loose, COACH_SCHEMA
from rehearsal.memory import connect, record_turn, watchlist, stats
from rehearsal.prompts import load_learner, load_scenarios
from rehearsal.session import practice
from rehearsal.srs import review
from rehearsal.report import build_html
from rehearsal.console import utf8_console

utf8_console()

ENGINE_TOML = "config/engine.toml"


def mock_engine() -> Engine:
    cfg = load_engine_config(ENGINE_TOML)
    cfg["mode"] = "mock"
    return Engine(cfg)


class Pipeline(unittest.TestCase):
    def test_mock_engine_emits_schema_json(self):
        raw = mock_engine().complete("sys", "user", schema=COACH_SCHEMA)
        parsed = parse_json_loose(raw, COACH_SCHEMA)
        self.assertIn("errors", parsed)
        self.assertEqual(parsed["errors"][0]["kind"], "pronunciation")

    def test_practice_loop_records_memory(self):
        con = connect()
        learner = load_learner("config/learner.toml")
        scenario = load_scenarios("config/scenarios")["cafe-aoi"]
        result = practice(mock_engine(), learner, scenario, con, max_turns=2,
                          script=["Ahara, sumisu no ogi, please.", "Katsu, please."])
        self.assertGreaterEqual(result["turns"], 1)
        self.assertGreaterEqual(result["corrections"], 1)
        self.assertTrue(watchlist(con))
        self.assertGreater(stats(con)["cards"], 0)

    def test_srs_grades_the_learners_own_sentence(self):
        con = connect()
        record_turn(con, "cafe-aoi", "sato please", "One sato?", {
            "understood": True, "level": 2,
            "errors": [{"said": "sato", "fix": "satoh",
                        "why": "final -s loanword needs the long vowel",
                        "kind": "pronunciation"}],
            "better": "Satoh, please.", "nudge": ""})
        out = review(con, n=1, auto=["satoh"])
        self.assertEqual(out, {"seen": 1, "right": 1})

    def test_report_names_the_friend(self):
        learner = load_learner("config/learner.toml")
        doc = build_html(learner)
        self.assertIn(learner["name"], doc)
        self.assertIn("<!doctype html>", doc)


if __name__ == "__main__":
    unittest.main()
