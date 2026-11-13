"""Menu tests drive menu.run with fake input; the file is a temp file."""
from __future__ import annotations

from pathlib import Path

import pytest

import menu
import storage
from storage import load_students, save_students


class Script:
    def __init__(self, lines):
        self.lines = list(lines)
        self.out: list[str] = []

    def ask(self, prompt):
        if not self.lines:
            raise EOFError
        return self.lines.pop(0)

    def say(self, text):
        self.out.append(text)

    @property
    def text(self):
        return "\n".join(self.out)


def go(path, lines):
    s = Script(lines)
    code = menu.run(s.ask, s.say, path)
    return code, s


def test_add_saves_to_file_immediately(tmp_path):
    p = tmp_path / "s.csv"
    code, s = go(p, ["1", "Anu", "80", "5"])
    assert code == 0 and "Added and saved" in s.text
    assert load_students(p) == [{"name": "Anu", "marks": 80}]


def test_book_is_remembered_between_runs(tmp_path):
    p = tmp_path / "s.csv"
    go(p, ["1", "Anu", "80", "1", "Ben", "70", "5"])
    code, s = go(p, ["2", "5"])
    assert "Anu - 80" in s.text and "Ben - 70" in s.text and "2 students loaded" in s.text


def test_remove_saves(tmp_path):
    p = tmp_path / "s.csv"
    go(p, ["1", "Anu", "80", "1", "Ben", "70", "4", "anu", "5"])
    assert load_students(p) == [{"name": "Ben", "marks": 70}]


def test_search_and_empty_messages(tmp_path):
    p = tmp_path / "s.csv"
    code, s = go(p, ["2", "3", "x", "5"])
    assert "The book is empty." in s.text and "No student matches." in s.text


def test_bad_input_shows_error_and_does_not_write(tmp_path):
    p = tmp_path / "s.csv"
    go(p, ["1", "", "5", "1", "Anu", "101", "1", "Anu", "x", "9", "5"])
    assert not p.exists()


def test_duplicate_rejected_and_file_unchanged(tmp_path):
    p = tmp_path / "s.csv"
    go(p, ["1", "Anu", "80", "5"])
    before = p.read_bytes()
    _, s = go(p, ["1", "ANU", "10", "5"])
    assert "already" in s.text and p.read_bytes() == before


def test_damaged_file_stops_before_menu_and_is_not_overwritten(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("name,marks\nAnu,abc\n", encoding="utf-8")
    before = p.read_bytes()
    code, s = go(p, ["1", "Ben", "5", "5"])
    assert code == 1 and "line 2" in s.text and "Student Book" not in s.text
    assert p.read_bytes() == before


def test_failed_save_keeps_memory_and_file_unchanged(tmp_path, monkeypatch):
    p = tmp_path / "s.csv"
    go(p, ["1", "Anu", "80", "5"])
    before = p.read_bytes()

    def boom(path, book):
        raise storage.StudentFileError("Could not save s.csv: disk full. The old file is unchanged.")

    monkeypatch.setattr(menu, "save_students", boom)
    _, s = go(p, ["1", "Ben", "70", "2", "5"])
    assert "Nothing was changed" in s.text
    assert "Ben" not in s.text.split("Nothing was changed")[-1]  # the list afterwards must not show Ben
    assert p.read_bytes() == before


def test_failed_remove_keeps_student(tmp_path, monkeypatch):
    p = tmp_path / "s.csv"
    go(p, ["1", "Anu", "80", "5"])
    monkeypatch.setattr(menu, "save_students", lambda *a: (_ for _ in ()).throw(storage.StudentFileError("x")))
    _, s = go(p, ["4", "Anu", "2", "5"])
    assert "Anu - 80" in s.text


def test_unknown_choice(tmp_path):
    _, s = go(tmp_path / "s.csv", ["9", "", "abc", "5"])
    assert s.text.count("Please type a number from 1 to 5.") == 3


@pytest.mark.parametrize("lines", [[], ["1"], ["1", "Anu"], ["3"], ["4"]])
def test_end_of_input_is_clean_exit(tmp_path, lines):
    code, s = go(tmp_path / "s.csv", lines)
    assert code == 0 and "Input ended" in s.text


def test_main_uses_env_file_and_ends_cleanly(tmp_path, monkeypatch, capsys):
    p = tmp_path / "env.csv"
    monkeypatch.setenv("STUDENTS_CSV", str(p))
    monkeypatch.setattr("builtins.input", lambda prompt="": (_ for _ in ()).throw(EOFError))
    assert menu.main() == 0
    assert "Traceback" not in capsys.readouterr().out


def test_default_file_is_next_to_script():
    assert menu.DEFAULT_FILE == Path(menu.__file__).resolve().parent / "students.csv"
