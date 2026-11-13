# Student Book That Remembers: Saving to a CSV File Safely

**Day 3 Mini Capstone, Student Book That Remembers (Files and Errors)**  
**Project folder:** `student-book-remembers`

---

## 1. Goal

Take the Day 2 class book and make it **remember** its students between runs, in a CSV file called `students.csv`.

From the task:
- On start, load the file. A missing file means a new empty book.
- Every add and every remove saves the file.
- A damaged file: say what is wrong and stop. Never overwrite it.
- Marks are whole numbers 0 to 100, names cannot be empty, `Anu` and `anu` are the same student, search is by part of a name ignoring capitals.
- File code in one module, the menu in another. Use a venv and list packages in `requirements.txt`.
- Ending the input (Ctrl+D, or Ctrl+Z then Enter) must not show a traceback.

I did the mini capstone from the course screenshot. The Aspect 18 exercises are yours; I did not solve them.

Think of a paper register in a drawer. Closing the program is closing the drawer. The file is the register itself, so the rule is: **never write on the register until you are sure the new page is complete**.

---

## 2. Tools

| Tool | Role |
|---|---|
| Python 3.10+ (tested on 3.13) | The program. Standard library only: `csv`, `pathlib`, `tempfile`, `os`. |
| pytest 9.1.1 | Tests |
| mypy 2.4.1 | Type check (clean) |

---

## 3. Project structure

```
student-book-remembers/
├── book.py        (the rules: names, marks, add, remove, search, sort; no files, no printing)
├── storage.py     (load_students, save_students, StudentFileError; all CSV knowledge)
├── menu.py        (the menu; run it with: python menu.py)
├── tests/         (82 tests: book, storage, menu, a real run)
├── break_it.py    (38 deliberate mistakes)
├── requirements.txt  requirements-dev.txt  pytest.ini  .gitignore
├── NOT_COVERED.md  README.md  DOCUMENTATION.md
```

---

## 4. Setup commands

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

**Commands**

```bash
python menu.py                 # run the menu (uses students.csv next to menu.py)
python -m pytest -q            # 82 tests (81 pass, 1 is skipped on some machines, see below)
python -m mypy book.py storage.py menu.py
python break_it.py             # 38 deliberate mistakes
```

---

## 5. How it works

| Piece | Job |
|---|---|
| `book.py` | Day 2 rules. Values in, values out, or `BookError`. Knows nothing about files |
| `load_students(path)` | missing file: empty book. Otherwise reads with `utf-8-sig`, checks header and every row, builds the book **through `add_student`** so file rows follow the same rules as typed rows |
| `save_students(path, book)` | writes a temp file in the same folder, flushes, then `os.replace` swaps it in. If anything fails the old file is still there and the temp file is removed |
| `menu.run(ask, say, path)` | loads first (a damaged file stops here, exit code 1). Then add and remove work on a **copy**, save the copy, and only then keep the change |
| `StudentFileError` | the one error file code raises. Its message says the file name, the line and "It was not changed." |

**Answers to the "Check yourself" list**

| Situation | What happens |
|---|---|
| no file | new empty book; first add creates the file |
| empty file (0 bytes) | `students.csv is empty (it has no header line name,marks)...` and stop |
| header only | an empty book |
| bad marks | `students.csv line 3: Marks must be a whole number from 0 to 100. It was not changed.` |
| missing column | the header check names line 1; a row with one cell names its line and says it found 1 |
| short row | `line 2: expected 2 columns (name,marks) but found 1` |
| a name with a comma | saved as `"Anu, K",80`; loads back the same |
| a failed save | `Could not save students.csv: ... The old file is unchanged.` The menu says nothing was changed and the list afterwards does not show the new student |
| no input (Ctrl+D) | `Input ended. Goodbye.` and exit code 0, no traceback |

**Decisions I made where the task is silent**
- **Empty (0 byte) file is treated as damaged**, not as a new book, because a book that has lost its header probably lost its data. Delete the file to start fresh.
- **Header names** are matched ignoring capitals and spaces (`Name, MARKS` is accepted).
- **Blank lines** are ignored.
- **Duplicate names in the file** (`Anu` and `anu`) count as damage, with the line number.
- **The file lives next to `menu.py`**, not in whatever folder you ran the command from. Set the `STUDENTS_CSV` environment variable to use another file.
- `students.csv` is in `.gitignore` because it is your data, not code.

---

## 6. The code

### `book.py`

```python
"""The rules of the student book (from Day 2). No typing, no printing, no files: values in, values out, or BookError."""
from __future__ import annotations

from typing import TypedDict


class Student(TypedDict):
    name: str
    marks: int


class BookError(Exception):
    """Something cannot be used. The message is written for the person to read."""


def clean_name(text: str) -> str:
    name = " ".join(text.split())
    if not name:
        raise BookError("The name cannot be empty.")
    return name


def name_key(name: str) -> str:
    """Two names are the same student when their keys are equal: capitals and extra spaces do not count."""
    return " ".join(name.split()).casefold()


def parse_marks(text: str) -> int:
    cleaned = text.strip()
    if not (cleaned.isascii() and cleaned.isdigit()) or int(cleaned) > 100:
        raise BookError("Marks must be a whole number from 0 to 100.")
    return int(cleaned)


def add_student(book: list[Student], name_text: str, marks_text: str) -> Student:
    name = clean_name(name_text)
    marks = parse_marks(marks_text)
    if any(name_key(s["name"]) == name_key(name) for s in book):
        raise BookError(f"A student called {name} is already in the book.")
    student: Student = {"name": name, "marks": marks}
    book.append(student)
    return student


def sorted_students(book: list[Student]) -> list[Student]:
    """By name, ignoring capitals. The book itself is not changed."""
    return sorted(book, key=lambda s: (name_key(s["name"]), s["name"]))


def find_students(book: list[Student], text: str) -> list[Student]:
    needle = name_key(text)
    if not needle:
        raise BookError("Type some letters of the name to search for.")
    return [s for s in sorted_students(book) if needle in name_key(s["name"])]


def remove_student(book: list[Student], name_text: str) -> Student:
    key = name_key(clean_name(name_text))
    for student in book:
        if name_key(student["name"]) == key:
            book.remove(student)
            return student
    raise BookError(f"No student called {clean_name(name_text)} in the book.")


def describe(student: Student) -> str:
    return f"{student['name']} - {student['marks']}"
```

### `storage.py`

```python
"""Loading and saving the student book as a CSV file. All the file knowledge lives here.

The file has a header line `name,marks` and one student per line. A name with a comma is quoted by the csv module:
    "Anu, K",80
"""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from book import BookError, Student, add_student

HEADER = ["name", "marks"]


class StudentFileError(Exception):
    """The file cannot be read or saved. The message says what is wrong and where."""


def load_students(path: Path) -> list[Student]:
    """No file: a new empty book. A damaged file: StudentFileError (the file is never changed)."""
    if not path.exists():
        return []
    try:
        # utf-8-sig: a file saved by Excel starts with an invisible BOM mark that would spoil the first header word
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.reader(handle))
    except UnicodeDecodeError:
        raise StudentFileError(f"{path.name} is not readable text (it is not saved as UTF-8). It was not changed.") from None
    except (OSError, csv.Error) as problem:
        raise StudentFileError(f"{path.name} cannot be read: {problem}. It was not changed.") from None

    if not rows:
        raise StudentFileError(f"{path.name} is empty (it has no header line `name,marks`). Delete it to start a new book, or restore it. It was not changed.")
    header = [cell.strip().casefold() for cell in rows[0]]
    if header != HEADER:
        raise StudentFileError(f"{path.name} line 1: the header must be `name,marks` but it is `{','.join(rows[0])}`. It was not changed.")

    book: list[Student] = []
    for line_number, row in enumerate(rows[1:], start=2):
        if not row:  # a completely blank line (for example at the end of the file)
            continue
        if len(row) != 2:
            raise StudentFileError(f"{path.name} line {line_number}: expected 2 columns (name,marks) but found {len(row)}. It was not changed.")
        try:
            add_student(book, row[0], row[1])  # the same rules as typing it in
        except BookError as problem:
            raise StudentFileError(f"{path.name} line {line_number}: {problem} It was not changed.") from None
    return book


def save_students(path: Path, book: list[Student]) -> None:
    """Write to a temporary file in the same folder, then swap it in. If anything fails the old file is untouched."""
    temp_name = ""
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
            temp_name = handle.name
            writer = csv.writer(handle)
            writer.writerow(HEADER)
            for student in book:
                writer.writerow([student["name"], student["marks"]])
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)  # one step: readers see the old file or the new one, never half of it
    except (OSError, csv.Error) as problem:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise StudentFileError(f"Could not save {path.name}: {problem}. The old file is unchanged.") from None
```

### `menu.py`

```python
"""The menu of the student book that remembers.   Run it:  python menu.py

The file is next to this script (not in whatever folder you started from). Set STUDENTS_CSV to use another file.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable

from book import BookError, Student, add_student, describe, find_students, remove_student, sorted_students
from storage import StudentFileError, load_students, save_students

DEFAULT_FILE = Path(__file__).resolve().parent / "students.csv"

MENU = """
Student Book
  1. Add a student
  2. List students
  3. Search by part of a name
  4. Remove a student
  5. Quit"""


def run(ask: Callable[[str], str], say: Callable[[str], None], path: Path) -> int:
    """Returns the exit code: 0 normal, 1 if the file is damaged (the menu never starts)."""
    try:
        book = load_students(path)
    except StudentFileError as problem:
        say(f"Error: {problem}")
        return 1
    say(f"Using {path} ({len(book)} students loaded).")
    try:
        while True:
            say(MENU)
            choice = ask("Choose 1-5: ").strip()
            try:
                if choice == "1":
                    candidate = list(book)  # change a copy, save it, and only then keep the change
                    student = add_student(candidate, ask("Name: "), ask("Marks (0-100): "))
                    save_students(path, candidate)
                    book[:] = candidate
                    say(f"Added and saved {describe(student)}.")
                elif choice == "2":
                    say("\n".join(describe(s) for s in sorted_students(book)) or "The book is empty.")
                elif choice == "3":
                    found = find_students(book, ask("Search for: "))
                    say("\n".join(describe(s) for s in found) or "No student matches.")
                elif choice == "4":
                    candidate = list(book)
                    removed = remove_student(candidate, ask("Name to remove: "))
                    save_students(path, candidate)
                    book[:] = candidate
                    say(f"Removed and saved {describe(removed)}.")
                elif choice == "5":
                    say("Goodbye.")
                    return 0
                else:
                    say("Please type a number from 1 to 5.")
            except BookError as problem:
                say(f"Error: {problem}")
            except StudentFileError as problem:
                say(f"Error: {problem} Nothing was changed.")
    except EOFError:  # the input ended (Ctrl+D, or Ctrl+Z then Enter on Windows)
        say("\nInput ended. Goodbye.")
        return 0


def main() -> int:
    return run(input, print, Path(os.environ.get("STUDENTS_CSV", DEFAULT_FILE)))


if __name__ == "__main__":
    sys.exit(main())
```

### `requirements.txt`

```text
# The program needs no packages besides Python itself.
# If you add one later, list it here with its version, for example:  requests==2.32.3
```

### `requirements-dev.txt`

```text
-r requirements.txt
pytest==9.1.1
mypy==2.4.1
```

### `pytest.ini`

```ini
[pytest]
pythonpath = .
testpaths = tests
```

### `break_it.py`

```python
"""Break the code on purpose, one rule at a time, and check that the tests notice.

Run from the project folder:   python break_it.py            (all cases)
                          or   python break_it.py word ...   (only cases whose name contains a word)

Each case edits one file, runs the tests, expects them to FAIL, then puts the file back.
A test run that hangs or runs out of time also counts as caught.
"""
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
LIMIT = 60  # seconds for one test run
CMD = [sys.executable, "-B", "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"]

# (name, file, old text that appears exactly once, new text)
CASES = [
    ('marks upper bound 100->101', 'book.py', 'int(cleaned) > 100', 'int(cleaned) > 101'),
    ('marks allow unicode digits', 'book.py', 'cleaned.isascii() and cleaned.isdigit()', 'cleaned.isdigit()'),
    ('name_key casefold->lower', 'book.py', 'return " ".join(name.split()).casefold()', 'return " ".join(name.split()).lower()'),
    ('name_key no space collapse', 'book.py', 'return " ".join(name.split()).casefold()', 'return name.casefold()'),
    ('duplicate check removed', 'book.py', 'if any(name_key(s["name"]) == name_key(name) for s in book):', 'if False:'),
    ('duplicate check case-sensitive', 'book.py', 'if any(name_key(s["name"]) == name_key(name) for s in book):', 'if any(s["name"] == name for s in book):'),
    ('empty name allowed', 'book.py', 'if not name:', 'if False:'),
    ('sort by case', 'book.py', 'key=lambda s: (name_key(s["name"]), s["name"])', 'key=lambda s: s["name"]'),
    ('search case-sensitive', 'book.py', 'if needle in name_key(s["name"])]', 'if text in s["name"]]'),
    ('search empty allowed', 'book.py', 'if not needle:', 'if False:'),
    ('remove ignores nothing', 'book.py', 'if name_key(student["name"]) == key:', 'if student["name"] == key:'),
    ('load: BOM encoding', 'storage.py', 'encoding="utf-8-sig"', 'encoding="utf-8"'),
    ('load: missing file error', 'storage.py', 'if not path.exists():\n        return []', "if not path.exists():\n        raise StudentFileError('missing')"),
    ('load: empty file ok', 'storage.py', 'if not rows:', 'if False:'),
    ('load: header unchecked', 'storage.py', 'if header != HEADER:', 'if False:'),
    ('load: header case sensitive', 'storage.py', '.casefold() for cell in rows[0]]', ' for cell in rows[0]]'),
    ('load: row length unchecked', 'storage.py', 'if len(row) != 2:', 'if False:'),
    ('load: wrong line number', 'storage.py', 'start=2)', 'start=1)'),
    ('load: blank lines fatal', 'storage.py', 'if not row:  # a completely blank line (for example at the end of the file)\n            continue', 'pass'),
    ('load: bad value swallowed', 'storage.py', 'raise StudentFileError(f"{path.name} line {line_number}: {problem} It was not changed.") from None', 'continue'),
    ('load: decode error uncaught', 'storage.py', 'except UnicodeDecodeError:', 'except ZeroDivisionError:'),
    ('save: no header', 'storage.py', 'writer.writerow(HEADER)', 'pass'),
    ('save: skip replace', 'storage.py', 'os.replace(temp_name, path)', 'pass'),
    ('save: temp file in the book folder is not the target', 'storage.py', 'os.replace(temp_name, path)', 'os.replace(temp_name, temp_name)'),
    ('save: no cleanup of temp', 'storage.py', 'os.unlink(temp_name)', 'pass'),
    ('save: error not wrapped', 'storage.py', 'except (OSError, csv.Error) as problem:\n        if temp_name:', 'except ZeroDivisionError as problem:\n        if temp_name:'),
    ('save: manual join not csv', 'storage.py', 'writer.writerow([student["name"], student["marks"]])', 'handle.write(student["name"] + "," + str(student["marks"]) + "\\n")'),
    ('save: utf-8 -> ascii', 'storage.py', '"w", encoding="utf-8", newline=""', '"w", encoding="ascii", newline=""'),
    ('menu: add saves nothing', 'menu.py', '                    save_students(path, candidate)\n                    book[:] = candidate\n                    say(f"Added', '                    book[:] = candidate\n                    say(f"Added'),
    ('menu: remove saves nothing', 'menu.py', '                    save_students(path, candidate)\n                    book[:] = candidate\n                    say(f"Removed', '                    book[:] = candidate\n                    say(f"Removed'),
    ('menu: add changes book before save', 'menu.py', 'candidate = list(book)  # change a copy, save it, and only then keep the change', 'candidate = book'),
    ('menu: file error not caught', 'menu.py', 'except StudentFileError as problem:\n                say(f"Error: {problem} Nothing', 'except ZeroDivisionError as problem:\n                say(f"Error: {problem} Nothing'),
    ('menu: EOF not caught', 'menu.py', 'except EOFError:  # the input', 'except ZeroDivisionError:  # the input'),
    ('menu: damaged file continues', 'menu.py', '        say(f"Error: {problem}")\n        return 1', '        say(f"Error: {problem}")\n        book = []'),
    ('menu: damaged exit code 0', 'menu.py', '        return 1\n    say(f"Using', '        return 0\n    say(f"Using'),
    ('menu: default file in cwd', 'menu.py', 'Path(__file__).resolve().parent / "students.csv"', 'Path("students.csv")'),
    ('menu: env var ignored', 'menu.py', 'Path(os.environ.get("STUDENTS_CSV", DEFAULT_FILE))', 'DEFAULT_FILE'),
    ('menu: quit returns 1', 'menu.py', 'say("Goodbye.")\n                    return 0', 'say("Goodbye.")\n                    return 1'),
]


def tests_fail() -> bool:
    for cache in ROOT.rglob("__pycache__"):  # an old compiled copy of a file we just changed would hide the change
        shutil.rmtree(cache, ignore_errors=True)
    try:
        return subprocess.run(CMD, cwd=ROOT, capture_output=True, text=True, timeout=LIMIT).returncode != 0
    except subprocess.TimeoutExpired:
        return True


def main(words: list[str]) -> None:
    chosen = [c for c in CASES if not words or any(w.lower() in c[0].lower() for w in words)]
    assert not tests_fail(), "the tests must pass before anything is broken"
    survivors = []
    for name, file, old, new in chosen:
        path = ROOT / file
        original = path.read_text(encoding="utf-8")
        if original.count(old) != 1:
            print(f"BAD CASE (text found {original.count(old)} times): {name}")
            survivors.append(name)
            continue
        try:
            path.write_text(original.replace(old, new), encoding="utf-8")
            caught = tests_fail()
        finally:
            path.write_text(original, encoding="utf-8")
        print(("caught   " if caught else "MISSED   ") + name, flush=True)
        if not caught:
            survivors.append(name)
    assert not tests_fail(), "files were not restored"
    print(f"\n{len(chosen) - len(survivors)} of {len(chosen)} mistakes caught")
    if survivors:
        print("NOT caught:", *survivors, sep="\n  - ")
        sys.exit(1)


main(sys.argv[1:])
```

### `NOT_COVERED.md`

```markdown
# What is NOT covered (Day 3: Student Book That Remembers)

Be honest about the gaps. These are things the tests do not prove.

- **Windows was not tested.** Everything was run on Linux. The code uses `pathlib`, `os.replace` and `utf-8-sig`, which work on Windows, and the run steps use PowerShell, but I did not run it there.
- **Two programs at once.** If two copies of the menu run at the same time, the last save wins. There is no lock file.
- **Power cut during a save.** The save writes a temp file, flushes it, then swaps it in. That is safe against a normal failure. I did not test a real power cut.
- **Very large files.** The whole file is read into memory. Tested with a handful of rows only.
- **Read-only folder test is skipped when running as root** (the sandbox runs as root, so folder permissions are ignored). It runs for a normal user. The failed-save behaviour is covered a different way (the swap step is made to fail on purpose).
- **Equivalent change the break script cannot see:** `newline=""` on reading. The csv module copes with line endings either way for rows that cannot contain a line break (names are cleaned, so they never do).
- **A temp-file name prefix** has no visible effect, so a change there cannot be caught by any test.
- **Odd text encodings** other than UTF-8 / UTF-8 with BOM (for example UTF-16 saved by Notepad) are reported as "not readable text", not converted.
- **The menu text** is checked for key words only, not word for word.
```

### `.gitignore`

```text
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.env
*.pyc
students.csv
*.tmp
```

### Design decisions

| Decision | Reason |
|---|---|
| Save to a temp file, then `os.replace` | The old file is only replaced by a complete new one. A crash mid-write cannot leave half a register. |
| Load builds the book through `add_student` | One set of rules for typed and file data; no second copy of the rules to forget. |
| Menu changes a copy, saves, then keeps it | If saving fails, memory and file still agree. Without this the screen would show a student the file does not have. |
| One `StudentFileError` for file problems | The menu catches one type and prints one message; no `except Exception`. |
| `utf-8-sig` when reading, `utf-8` when writing | Excel adds an invisible mark at the start of a file; this reads it, but never writes it. |
| `newline=""` with the csv module | The csv module handles line endings itself (Windows `\r\n` and Linux `\n` both load). |
| Path comes from `Path(__file__)` | The book does not move when you start the program from another folder. |

---

## 7. Tests (82 tests)

| Group | Tests | What it proves |
|---|---|---|
| `test_book.py` | 27 | marks edges, empty names, duplicates in other capitals, sort and search ignoring capitals, remove |
| `test_storage.py` | 34 | no file, empty file, header only, bad marks (8 kinds), missing column, short and long rows, BOM, Windows line endings, comma and quote in a name, accented names, not-UTF-8, a folder instead of a file, damaged file left byte-for-byte unchanged, save round trip, no leftover temp files, failed save, failure halfway through writing |
| `test_menu.py` | 17 | add and remove save at once, remembered between runs, bad input writes nothing, duplicates, damaged file stops before the menu, a failed save changes nothing, input ending at 5 places |
| `test_real_run.py` | 3 | the real program in a separate process: no traceback on no input, two runs remember, damaged file gives exit code 1 and stays untouched |
| `test_notes_exist.py` | 1 | NOT_COVERED.md is there |

| # | Test | What it proves |
|---|---|---|
| 1 | `test_failure_halfway_through_writing_keeps_old_file` | the writer breaks on the 3rd row; the old file is byte-for-byte the same and no temp file is left |
| 2 | `test_failed_save_keeps_memory_and_file_unchanged` | a failed save: the list afterwards does not show the new student, and the file is unchanged |

### `tests/test_storage.py`

```python
"""File tests: load and save are called directly, no menu involved."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

import storage
from storage import StudentFileError, load_students, save_students


def write(path: Path, text: str, encoding: str = "utf-8") -> Path:
    path.write_bytes(text.encode(encoding))
    return path


def test_missing_file_is_new_empty_book(tmp_path):
    assert load_students(tmp_path / "none.csv") == []


def test_empty_file_is_reported(tmp_path):
    p = write(tmp_path / "s.csv", "")
    with pytest.raises(StudentFileError, match="empty"):
        load_students(p)
    assert p.read_bytes() == b""


def test_header_only_is_empty_book(tmp_path):
    assert load_students(write(tmp_path / "s.csv", "name,marks\n")) == []


def test_normal_rows(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu,80\nBen,0\nCy,100\n")
    assert load_students(p) == [{"name": "Anu", "marks": 80}, {"name": "Ben", "marks": 0}, {"name": "Cy", "marks": 100}]


def test_header_case_and_spaces_tolerated(tmp_path):
    assert load_students(write(tmp_path / "s.csv", " Name , MARKS \nAnu,5\n")) == [{"name": "Anu", "marks": 5}]


def test_bom_file_from_excel(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu,80\n", "utf-8-sig")
    assert p.read_bytes().startswith(b"\xef\xbb\xbf")
    assert load_students(p) == [{"name": "Anu", "marks": 80}]


def test_crlf_line_endings(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\r\nAnu,80\r\nBen,70\r\n")
    assert [s["name"] for s in load_students(p)] == ["Anu", "Ben"]


def test_blank_line_at_end_and_middle_ignored(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu,80\n\nBen,70\n\n")
    assert len(load_students(p)) == 2


def test_name_with_comma_round_trip(tmp_path):
    p = tmp_path / "s.csv"
    save_students(p, [{"name": "Anu, K", "marks": 80}])
    assert '"Anu, K"' in p.read_text(encoding="utf-8")
    assert load_students(p) == [{"name": "Anu, K", "marks": 80}]


def test_name_with_quote_and_unicode_round_trip(tmp_path):
    p = tmp_path / "s.csv"
    book = [{"name": 'Ann "Annie" Lee', "marks": 1}, {"name": "Zoë Ñandú", "marks": 99}]
    save_students(p, book)
    assert load_students(p) == book


@pytest.mark.parametrize("bad", ["-1", "101", "x", "", "3.5", "True", "٣", "1e2"])
def test_bad_marks_name_the_line(tmp_path, bad):
    p = write(tmp_path / "s.csv", f"name,marks\nAnu,80\nBen,{bad}\n")
    with pytest.raises(StudentFileError, match="line 3"):
        load_students(p)


def test_missing_column_header(tmp_path):
    p = write(tmp_path / "s.csv", "name\nAnu\n")
    with pytest.raises(StudentFileError, match="line 1"):
        load_students(p)


def test_wrong_header_names(tmp_path):
    with pytest.raises(StudentFileError, match="header"):
        load_students(write(tmp_path / "s.csv", "student,score\nAnu,5\n"))


def test_short_row(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu\n")
    with pytest.raises(StudentFileError, match=r"line 2.*found 1"):
        load_students(p)


def test_long_row(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu,5,extra\n")
    with pytest.raises(StudentFileError, match=r"line 2.*found 3"):
        load_students(p)


def test_empty_name_in_file(tmp_path):
    with pytest.raises(StudentFileError, match="line 2"):
        load_students(write(tmp_path / "s.csv", "name,marks\n  ,5\n"))


def test_duplicate_names_in_file(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu,5\nanu,6\n")
    with pytest.raises(StudentFileError, match="line 3"):
        load_students(p)


def test_not_utf8_file(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nZoë,5\n", "latin-1")
    with pytest.raises(StudentFileError, match="UTF-8"):
        load_students(p)


def test_path_is_a_folder(tmp_path):
    d = tmp_path / "s.csv"
    d.mkdir()
    with pytest.raises(StudentFileError):
        load_students(d)


def test_damaged_file_is_never_changed(tmp_path):
    p = write(tmp_path / "s.csv", "name,marks\nAnu,5\nBen,oops\n")
    before = p.read_bytes()
    with pytest.raises(StudentFileError):
        load_students(p)
    assert p.read_bytes() == before


def test_save_then_load_round_trip(tmp_path):
    p = tmp_path / "s.csv"
    book = [{"name": "Anu", "marks": 80}, {"name": "Ben", "marks": 0}]
    save_students(p, book)
    assert p.read_text(encoding="utf-8").splitlines()[0] == "name,marks"
    assert load_students(p) == book


def test_save_empty_book_writes_header_only(tmp_path):
    p = tmp_path / "s.csv"
    save_students(p, [])
    assert p.read_text(encoding="utf-8").strip() == "name,marks"
    assert load_students(p) == []


def test_save_replaces_old_content_and_leaves_no_temp_files(tmp_path):
    p = tmp_path / "s.csv"
    save_students(p, [{"name": "Anu", "marks": 1}])
    save_students(p, [{"name": "Ben", "marks": 2}])
    assert load_students(p) == [{"name": "Ben", "marks": 2}]
    assert [f.name for f in tmp_path.iterdir()] == ["s.csv"]


def test_failed_save_keeps_old_file_and_cleans_up(tmp_path, monkeypatch):
    p = tmp_path / "s.csv"
    save_students(p, [{"name": "Anu", "marks": 1}])
    before = p.read_bytes()

    def boom(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(storage.os, "replace", boom)
    with pytest.raises(StudentFileError, match="old file is unchanged"):
        save_students(p, [{"name": "Zed", "marks": 9}])
    assert p.read_bytes() == before
    assert [f.name for f in tmp_path.iterdir()] == ["s.csv"]


def test_save_into_missing_folder_is_reported(tmp_path):
    with pytest.raises(StudentFileError, match="Could not save"):
        save_students(tmp_path / "nope" / "s.csv", [])


@pytest.mark.skipif(os.name == "nt", reason="folder permissions work differently on Windows")
@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores folder permissions")
def test_save_into_read_only_folder(tmp_path):
    d = tmp_path / "ro"
    d.mkdir()
    d.chmod(0o500)
    try:
        with pytest.raises(StudentFileError):
            save_students(d / "s.csv", [])
    finally:
        d.chmod(0o700)


def test_failure_halfway_through_writing_keeps_old_file(tmp_path, monkeypatch):
    p = tmp_path / "s.csv"
    save_students(p, [{"name": "Old", "marks": 1}])
    before = p.read_bytes()
    real_writer = storage.csv.writer

    class Breaks:
        def __init__(self, handle):
            self.inner, self.calls = real_writer(handle), 0

        def writerow(self, row):
            self.calls += 1
            if self.calls == 3:
                raise OSError("disk full")
            self.inner.writerow(row)

    monkeypatch.setattr(storage.csv, "writer", Breaks)
    with pytest.raises(StudentFileError):
        save_students(p, [{"name": n, "marks": 1} for n in "ABCD"])
    assert p.read_bytes() == before
    assert [f.name for f in tmp_path.iterdir()] == ["s.csv"]
```

### `tests/test_menu.py`

```python
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
```

---

## 8. Results

| Check | Command | Result |
|---|---|---|
| Tests | `python -m pytest -q` | **81 passed, 1 skipped** (the skipped one needs a normal user account, not root) |
| Type check | `python -m mypy book.py storage.py menu.py` | **no issues found** |
| Break it on purpose | `python break_it.py` | **38 of 38 caught** (first run 36 of 39: two were weak tests, one an equivalent change; fixed and listed in NOT_COVERED.md) |
| Clean unzip | fresh folder, new venv, tests | see the final message |

---

## 9. Problems avoided

| Problem | Cause | Fix |
|---|---|---|
| First header word did not match when saved by Excel | Excel puts an invisible BOM at the start | Read with `utf-8-sig` |
| Screen could show a student the file did not have | Changing the list before saving | Change a copy, save, then keep it |
| Sort test passed even with a wrong sort | Test names all started with the same capital pattern | Test uses `bob, Cy, anu, Ann`, where capitals change the order |
| Break-it left a `students.csv` in the project folder | A deliberate mistake made the program ignore `STUDENTS_CSV` | Deleted it; the file is in `.gitignore` |

---

## 10. What was practiced

- `csv.reader` and `csv.writer`
- `pathlib.Path`
- Encodings, BOM and `utf-8-sig`
- Temp file and `os.replace` (safe save)
- One custom exception for one kind of problem
- `tmp_path` and `monkeypatch` in pytest
- Splitting code into modules

---

## 11. Known limit

- **Windows was not tested.** Everything ran on Linux with Python 3.13.
- **No lock.** Two copies of the menu at once: the last save wins.
- The whole file is read into memory (fine for a class, not for millions of rows).
- One test is skipped when run as `root`. It runs for a normal user.
- Full list in `NOT_COVERED.md`.

---

## 12. How to run it

```bash
# Windows PowerShell, from the folder that holds student-book-remembers.zip
Expand-Archive student-book-remembers.zip -DestinationPath .
cd student-book-remembers
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m pytest -q
python menu.py
```

Try it: add `Anu, K` with 80, choose 5, run again, and see it is still there. Then open students.csv in a text editor, break a mark on purpose, and run again.
