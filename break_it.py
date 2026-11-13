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
