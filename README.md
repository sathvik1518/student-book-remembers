# Student Book That Remembers

The Day 2 class book, now saved to `students.csv`. Loads on start (missing file = empty book), saves on every add and remove, and refuses to touch a damaged file.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python menu.py
python -m pytest -q          # 82 tests
python break_it.py           # 38 deliberate mistakes
```

`book.py` has the rules, `storage.py` the file code, `menu.py` the menu. Read `NOT_COVERED.md` for the gaps.

See `DOCUMENTATION.md` for the full write-up.
