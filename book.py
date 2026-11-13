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
