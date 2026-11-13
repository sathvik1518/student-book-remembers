"""Runs menu.py as a real program (a separate process), the way a person would."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(tmp_path, stdin, csv=None):
    env = {**os.environ, "STUDENTS_CSV": str(csv or tmp_path / "s.csv")}
    return subprocess.run([sys.executable, "-B", str(ROOT / "menu.py")], input=stdin, capture_output=True, text=True, env=env, timeout=30)


def test_no_input_at_all_shows_no_traceback(tmp_path):
    r = run(tmp_path, "")
    assert r.returncode == 0 and "Traceback" not in r.stderr + r.stdout


def test_two_separate_runs_remember(tmp_path):
    run(tmp_path, "1\nAnu\n80\n5\n")
    r = run(tmp_path, "2\n5\n")
    assert "Anu - 80" in r.stdout


def test_damaged_file_exit_code_1_and_untouched(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("name,marks\nAnu\n", encoding="utf-8")
    r = run(tmp_path, "1\nBen\n5\n5\n", csv=p)
    assert r.returncode == 1 and "line 2" in r.stdout and "Traceback" not in r.stderr
    assert p.read_text(encoding="utf-8") == "name,marks\nAnu\n"
