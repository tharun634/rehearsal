"""Entry point so the tool needs no `pip install -e .` and no PYTHONPATH.

    python run.py doctor
    python run.py practice --scenario cafe-aoi
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "src"))

from rehearsal.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
