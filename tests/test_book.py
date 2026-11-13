from __future__ import annotations

import pytest

from book import BookError, add_student, clean_name, find_students, name_key, parse_marks, remove_student, sorted_students


@pytest.mark.parametrize("text,expected", [("0", 0), ("100", 100), (" 55 ", 55), ("007", 7)])
def test_parse_marks_ok(text, expected):
    assert parse_marks(text) == expected


@pytest.mark.parametrize("text", ["-1", "101", "x", "", " ", "3.5", "1e2", "٣", "+5", "True"])
def test_parse_marks_bad(text):
    with pytest.raises(BookError, match="0 to 100"):
        parse_marks(text)


def test_clean_name_collapses_spaces():
    assert clean_name("  Anu   K ") == "Anu K"


@pytest.mark.parametrize("text", ["", "   ", "\t"])
def test_empty_name(text):
    with pytest.raises(BookError, match="empty"):
        clean_name(text)


def test_name_key_ignores_capitals_and_spaces():
    assert name_key("ANU  k") == name_key("anu K") == "anu k"
    assert name_key("Straße") == name_key("STRASSE")


def test_add_returns_student_and_keeps_it():
    book = []
    s = add_student(book, " Anu ", "80")
    assert s == {"name": "Anu", "marks": 80} and book == [s]


def test_duplicate_ignoring_capitals():
    book = []
    add_student(book, "Anu", "80")
    with pytest.raises(BookError, match="already"):
        add_student(book, "anu", "70")
    assert len(book) == 1


def test_failed_add_changes_nothing():
    book = []
    for name, marks in [("", "5"), ("Anu", "x"), ("Anu", "101")]:
        with pytest.raises(BookError):
            add_student(book, name, marks)
    assert book == []


def test_sorted_ignores_capitals_and_leaves_book_alone():
    book = []
    for n in ["bob", "Cy", "anu", "Ann"]:
        add_student(book, n, "1")
    assert [s["name"] for s in sorted_students(book)] == ["Ann", "anu", "bob", "Cy"]
    assert [s["name"] for s in book] == ["bob", "Cy", "anu", "Ann"]


def test_find_by_part_ignoring_capitals():
    book = []
    for n in ["Anu", "Hannah", "Bob"]:
        add_student(book, n, "1")
    assert [s["name"] for s in find_students(book, "AN")] == ["Anu", "Hannah"]
    assert find_students(book, "zzz") == []


def test_find_empty_text_is_an_error():
    with pytest.raises(BookError):
        find_students([], "  ")


def test_remove_ignores_capitals():
    book = []
    add_student(book, "Anu", "5")
    assert remove_student(book, "ANU")["name"] == "Anu"
    assert book == []


def test_remove_unknown():
    with pytest.raises(BookError, match="No student"):
        remove_student([], "Zed")
