#!/usr/bin/env python3
"""Guard: every RFC file has a README index row, and every index row resolves.

Catches the class of bug where an RFC merges without its `rfcs/README.md`
index entry (0018 shipped unreachable from the index; 0019's PR repeated it)
and the reverse — an index row left pointing at a renamed or deleted file.

Run locally from anywhere:
    python3 scripts/check_rfc_index.py
Exits 1 with a readable list on any mismatch. Stdlib only.
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
RFCS = ROOT / "rfcs"
README = RFCS / "README.md"

# The template is not an RFC; its pseudo-row in the index is informational
# and not a link, so it is exempt from the link-format contract.
EXCLUDE = {"0000-template.md"}


def main() -> int:
    pattern = "[0-9][0-9][0-9][0-9]-*.md"
    files = {p.name for p in RFCS.glob(pattern)} - EXCLUDE

    if not README.is_file():
        print(f"RFC index check failed: {README} not found")
        return 1
    text = README.read_text(encoding="utf-8")

    # Index rows look like:
    # | [0018](./0018-startup-loading-states.md) | Title | status | platforms |
    row_re = re.compile(r"^\|\s*\[(\d{4})\]\(\./([^)]+)\)", re.M)

    problems: list[str] = []
    indexed: dict[str, str] = {}  # number -> linked filename
    order: list[str] = []
    for num, fname in row_re.findall(text):
        if num in indexed:
            problems.append(f"duplicate index row for {num}")
        indexed[num] = fname
        order.append(num)

    # Direction 1: file without a row (or the row points at a different file).
    for f in sorted(files):
        num = f.split("-", 1)[0]
        if num not in indexed:
            problems.append(f"rfcs/{f} exists but has no README index row")
        elif indexed[num] != f:
            problems.append(
                f"index row {num} points at {indexed[num]}, but the file is {f}"
            )

    # Direction 2: row without a file (renamed/deleted RFC).
    for num, fname in indexed.items():
        if not (RFCS / fname).is_file():
            problems.append(f"index row {num} links ./{fname}, which does not exist")

    # Ordering: rows should ascend; a shuffled index hides entries from scan-readers.
    if order != sorted(order):
        problems.append("index rows are not in ascending numeric order: " + ", ".join(order))

    if problems:
        print("RFC index check failed:")
        for p in problems:
            print(f"  - {p}")
        return 1

    print(f"RFC index OK ({len(files)} RFC files, {len(indexed)} index rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
