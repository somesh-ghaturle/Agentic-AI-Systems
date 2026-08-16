#!/usr/bin/env python3
"""Check every Terraform provider constraint under infra/ pins a major and agrees tree-wide.

    python3 .github/scripts/tfconstraints.py infra

Exits non-zero, listing file and line, if either rule is broken.

Standard library only, like every other check here — no HCL parser dependency, no `terraform`
binary, no network. Two rules, both of which exist because the repository broke them.

**Rule 1: no floors.** A provider constraint must pin a major (`~> 6.0`), never floor
(`>= 6.0`). This is REPO-AUDIT task 21. A floor is invisible to `terraform validate` — it
resolves perfectly well, it just resolves to something different next month — so nothing else
in CI notices. It also makes the `terraform` entry in dependabot.yml inert, since Dependabot
raises a constraint only when the constraint excludes the newest release.

`required_version` is deliberately exempt and stays `>= 1.6`. That is the Terraform CLI, not a
provider; capping the CLI to a major buys nothing and would strand anyone on a newer one.

**Rule 2: one constraint per provider.** Every `required_providers` block naming a given
source must give it the same constraint. This is the rule the first version of this check
lacked, and the omission surfaced within a day: Dependabot bumped `hashicorp/google` to
`~> 7.44` across 22 directories and left a tree-level `versions.tf` on `~> 6.0`, because that
directory is not one Dependabot maintains. A partial bump is the normal way this drifts — a
module added after the last bump, or a directory the tooling does not reach — and it produces
a tree where the roots and the modules disagree about what they are written against.

The orphan files that motivated rule 2 were deleted rather than fixed, on the grounds that
aligning them only holds until the next bump. The rule stays because the failure mode is
general: any module left behind on a future bump trips it.

Regex rather than a parser, which is worth stating plainly. `required_providers` bodies in
this repository are uniform, machine-written HCL — `source` then `version`, one provider per
block, no interpolation, no `configuration_aliases`. A parser would be more correct about HCL
this file will never see. If that stops being true, this check gets confused rather than
silently permissive: an unrecognised block yields no constraints and no findings, so the
failure mode is a rule that stops guarding, which the accompanying tests are what catch.
"""

import pathlib
import re
import sys

SKIP_DIRS = {".git", ".terraform", "__pycache__", "node_modules"}

# A `source = "hashicorp/google"` line followed, within a few lines, by its `version`. Both
# keys sit inside one provider block; matching them as a pair is what ties a constraint to
# the provider it constrains. `required_version` cannot match: the key here is exactly
# `version`, anchored to the start of its own line after leading whitespace.
PROVIDER = re.compile(
    r'^\s*source\s*=\s*"(?P<source>[^"]+)"\s*$'
    r"(?P<between>(?:\s*^\s*(?:#[^\n]*)?$)*)"
    r'\s*^\s*version\s*=\s*"(?P<constraint>[^"]+)"\s*$',
    re.MULTILINE,
)


def tf_files(root):
    for path in sorted(root.rglob("*.tf")):
        if SKIP_DIRS.isdisjoint(path.parts):
            yield path


def constraints(path):
    """Yield (lineno, source, constraint) for each provider declaration in `path`."""
    text = path.read_text(encoding="utf-8")
    for match in PROVIDER.finditer(text):
        lineno = text.count("\n", 0, match.start("constraint")) + 1
        yield lineno, match.group("source"), match.group("constraint")


def main():
    root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "infra").resolve()
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")

    # source -> constraint -> [(relative path, lineno)]
    seen = {}
    failures = []
    checked = 0

    for path in tf_files(root):
        checked += 1
        for lineno, source, constraint in constraints(path):
            relative = path.relative_to(root.parent)
            if constraint.startswith(">="):
                failures.append(
                    f"FLOOR    {relative}:{lineno} {source} = {constraint!r} "
                    f"— pin the major with ~>"
                )
            seen.setdefault(source, {}).setdefault(constraint, []).append((relative, lineno))

    for source, by_constraint in sorted(seen.items()):
        if len(by_constraint) > 1:
            spread = ", ".join(
                f"{c!r} in {len(sites)} file(s)" for c, sites in sorted(by_constraint.items())
            )
            failures.append(f"MISMATCH {source} declared {len(by_constraint)} ways: {spread}")
            for constraint, sites in sorted(by_constraint.items()):
                for relative, lineno in sites:
                    failures.append(f"         {relative}:{lineno} {constraint}")

    for line in failures:
        print(line)

    if failures:
        print(f"\nprovider constraint check failed across {checked} .tf files")
        print("see docs/REPO-AUDIT.md task 21")
        return 1

    total = sum(len(sites) for by in seen.values() for sites in by.values())
    print(f"{checked} .tf files checked, {total} provider constraints, {len(seen)} providers, all pinned and consistent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
