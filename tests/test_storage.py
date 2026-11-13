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
