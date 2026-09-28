#!/usr/bin/env python3
"""Assert every reference to a preset in this repo resolves to a file.

`renovate-config-validator` checks the syntax and schema of the file it is
given. It does NOT resolve `extends`: a reference to
`local>FlowMatrix-AI/renovate-config:no-such-preset` validates clean (#36). The
failure mode of a dangling reference is silence -- Renovate falls back and the
repos extending the preset quietly stop getting updates -- so it is checked
here instead.

Two rules:

1. Every `local>FlowMatrix-AI/renovate-config[:name]` reference in a preset or
   in README.md resolves to `<name>.json` (no name means `default.json`).
2. Every preset name in PUBLISHED still has a file. Consumer repos reference
   these by name from outside this repo, so renaming or deleting one breaks
   them with no error here. Removing a name from PUBLISHED is the deliberate
   step that says the consumers have been moved off it.

Usage: check-preset-references.py [ROOT]   (default: the repository root)
"""

import re
import sys
from pathlib import Path

# Preset names consumer repos extend today (counted from the org's renovate.json
# files on 2026-09-28: default 57, site-npmjs 7, marketing-site 6,
# npmjs-scope 4). Add a name here when a new preset is published.
PUBLISHED = ["default", "marketing-site", "npmjs-scope", "site-npmjs"]

# `local>` and `github>` both address this repo. An optional `//path`,
# `#tag` or `(args)` suffix is not used in this org and is not supported:
# a reference carrying one is reported rather than silently skipped.
REF = re.compile(
    r"(?:local|github)>FlowMatrix-AI/renovate-config(?::(?P<name>[A-Za-z0-9._/-]+))?(?P<rest>[^\s\"'`,\]]*)"
)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    presets = {p.stem for p in root.glob("*.json")}
    sources = sorted(root.glob("*.json")) + [root / "README.md"]

    failures, refs = [], 0
    for src in sources:
        if not src.exists():
            continue
        for lineno, line in enumerate(src.read_text().splitlines(), 1):
            for m in REF.finditer(line):
                refs += 1
                name = m.group("name") or "default"
                where = f"{src.name}:{lineno}"
                if m.group("rest"):
                    failures.append((src.name, lineno, f"unsupported suffix {m.group('rest')!r} on {m.group(0)!r}"))
                elif name not in presets:
                    failures.append((src.name, lineno, f"{m.group(0)!r} names preset '{name}', but there is no {name}.json"))
                else:
                    print(f"  ok    {where}: {m.group(0)} -> {name}.json")

    for name in PUBLISHED:
        if name in presets:
            print(f"  ok    published preset '{name}' -> {name}.json")
        else:
            failures.append(("", 0, f"published preset '{name}' has no {name}.json; consumer repos extending it would silently stop getting updates"))

    if not refs:
        print("::error::no preset references found -- this check would pass vacuously")
        return 1

    for fname, lineno, msg in failures:
        loc = f" file={fname},line={lineno}" if fname else ""
        print(f"::error{loc}::{msg}")
    if failures:
        return 1

    print(f"\n{refs} reference(s) and {len(PUBLISHED)} published preset(s) checked, all resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
