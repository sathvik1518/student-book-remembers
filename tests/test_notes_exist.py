from pathlib import Path


def test_not_covered_file_exists():
    assert (Path(__file__).resolve().parent.parent / "NOT_COVERED.md").read_text(encoding="utf-8").strip()
