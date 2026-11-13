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
