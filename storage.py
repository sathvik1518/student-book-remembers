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
