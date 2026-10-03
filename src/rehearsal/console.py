"""One place that fixes the Windows console.

Default Python on Windows writes cp1252; a Japanese turn or a ✓ crashes print.
Every entry point calls utf8_console() first.
"""
import io
import sys


def utf8_console() -> None:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8",
                                  errors="replace")
