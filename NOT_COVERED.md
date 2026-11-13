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
