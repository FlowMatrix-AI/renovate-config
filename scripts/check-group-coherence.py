#!/usr/bin/env python3
"""Assert every ecosystem group is repeated under `vulnerabilityAlerts`.

Renovate's built-in default for `vulnerabilityAlerts` sets `groupName: null`,
which OVERRIDES any groupName a `packageRules` entry applies. So an ecosystem
grouped for routine updates is silently UN-grouped for security updates -- and
a security advisory then arrives as a partial bump that does not build.

That is not hypothetical. Three `astro` 6->7 `[security]` PRs sat red for a
month each in 2026-07/08 for exactly this reason (checkout-site-engine#154),
and the preset that was supposed to prevent it (#26) validated clean the whole
time. `renovate-config-validator` cannot catch this: the config is well-formed,
just semantically incomplete.

Rule enforced: if a packageRules entry groups an explicit set of package names,
that same set must also be grouped under `vulnerabilityAlerts.packageRules`.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Groups that deliberately need no vulnerabilityAlerts counterpart, with the
# reason. Keep this small and justified -- it is the escape hatch, not a bin.
EXEMPT = {
    frozenset({"@flowmatrix-ai/**"}): (
        "private packages: the GitHub/OSV advisory databases do not cover them, "
        "so vulnerabilityAlerts can never fire for this set"
    ),
}


def package_sets_under_vulnerability_alerts(configs):
    """Every explicit package set grouped under vulnerabilityAlerts, any preset."""
    sets = []
    for cfg in configs.values():
        for rule in cfg.get("vulnerabilityAlerts", {}).get("packageRules", []):
            if rule.get("groupName") and "matchPackageNames" in rule:
                sets.append(frozenset(rule["matchPackageNames"]))
    return sets


def main() -> int:
    configs = {p.name: json.loads(p.read_text()) for p in sorted(ROOT.glob("*.json"))}
    covered = package_sets_under_vulnerability_alerts(configs)

    failures, checked = [], 0
    for name, cfg in configs.items():
        for rule in cfg.get("packageRules", []):
            # An "ecosystem group" = groups a named set of packages. Groups keyed
            # only on update type or manager (e.g. "npm non-major") are batching
            # conveniences, not sets that must move together, so they are skipped.
            if not rule.get("groupName") or "matchPackageNames" not in rule:
                continue
            names = frozenset(rule["matchPackageNames"])
            checked += 1
            if names in EXEMPT:
                print(f"  SKIP  {name}: {rule['groupName']} -- {EXEMPT[names]}")
                continue
            if any(names <= c for c in covered):
                print(f"  ok    {name}: {rule['groupName']} {sorted(names)}")
            else:
                failures.append((name, rule["groupName"], sorted(names)))

    if not checked:
        print("::error::no ecosystem groups found -- this check would pass vacuously")
        return 1

    for name, group, names in failures:
        print(
            f"::error file={name}::group '{group}' {names} is not repeated under "
            f"vulnerabilityAlerts.packageRules, so a security advisory on it will "
            f"arrive as an un-grouped partial bump. Add a matching rule there."
        )
    if failures:
        return 1

    print(f"\n{checked} ecosystem group(s) checked, all coherent under vulnerabilityAlerts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
