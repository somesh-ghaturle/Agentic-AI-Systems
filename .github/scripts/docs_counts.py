#!/usr/bin/env python3
"""Check the counts the documentation states against the counts the tree has.

    python3 .github/scripts/docs_counts.py .

Exits non-zero naming the file, the sentence, the number it claims, and the number that is
actually there.

Why this exists. `a2faa35` was titled "Fix eight stale claims found in full-repo sweep", and by
the next audit the README had drifted again -- it described twelve jobs when there were
fourteen, and twelve examples when there were twenty-three. Hand-fixing a count resets the
clock rather than stopping it, and prose is where this hides longest because nothing runs it.
That is the same argument every other script in this directory makes about its own subject.

Adding a claim. Put it in CLAIMS with a regex holding exactly one capture group around the
number. Both digits and number words up to twenty-four are understood, because this repository
writes small numbers as words in prose and as digits in tables. A claim whose regex stops
matching is a failure, not a skip: rewording the sentence is exactly when the number needs
looking at again.

Standard library only, like every other check here.
"""

import pathlib
import re
import sys

_WORDS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty", "twenty-one", "twenty-two", "twenty-three", "twenty-four",
)
WORDS = {w: i for i, w in enumerate(_WORDS)}


def to_int(token):
    token = token.strip().lower()
    if token.isdigit():
        return int(token)
    return WORDS.get(token)


def counts(root):
    examples = sorted(d for d in (root / "examples").iterdir() if d.is_dir())
    tests = root / "tests"
    suites = [
        d for d in examples if (tests / f"test_{d.name.replace('-', '_')}.py").exists()
    ]

    reqs = [d for d in examples if (d / "requirements.txt").exists()]
    stdlib_only = []
    for d in reqs:
        lines = (d / "requirements.txt").read_text().splitlines()
        if not [ln for ln in (x.strip() for x in lines) if ln and not ln.startswith("#")]:
            stdlib_only.append(d)

    # A narrow read of the workflow rather than a YAML parse: job names are the only keys at
    # exactly two spaces of indentation after the top-level `jobs:` line. Adding PyYAML for
    # this would be the one dependency in a directory that has none.
    checks = (root / ".github/workflows/checks.yml").read_text().splitlines()
    jobs, in_jobs = 0, False
    for line in checks:
        if line.startswith("jobs:"):
            in_jobs = True
            continue
        if in_jobs:
            if line and not line[0].isspace():
                break
            if re.fullmatch(r"  [a-z][a-z0-9-]*:", line.rstrip()):
                jobs += 1

    deps = (root / ".github/workflows/example-deps.yml").read_text()
    deps_legs = len(re.findall(r"^\s*- example:", deps, re.M))
    plan = (root / "docs/ENHANCEMENT-PLAN.md").read_text()
    plan_tasks = len(re.findall(r"^\| \d+ \|", plan, re.M))

    return {
        "examples": len(examples),
        "suites": len(suites),
        "reqs": len(reqs),
        "stdlib_only": len(stdlib_only),
        "jobs": jobs,
        "deps_legs": deps_legs,
        "plan_tasks": plan_tasks,
        "diagrams": len(list((root / "docs/diagrams").glob("*.html"))),
    }


# (file, key, regex with ONE group around the number, what the sentence is about)
CLAIMS = [
    ("README.md", "jobs", r"own scripts — (\S+) jobs, checking", "jobs in checks.yml"),
    ("README.md", "suites", r"tests/` — (\S+) of the \S+ examples, via",
     "examples with a suite"),
    ("README.md", "examples", r"suites under `tests/` — \S+ of the (\S+) examples", "examples"),
    ("README.md", "examples", r"syntax check over all (\S+) examples", "examples"),
    ("README.md", "deps_legs", r"entry modules — the (\S+) that carry dependencies",
     "example-deps matrix legs"),
    ("CONTRIBUTING.md", "stdlib_only",
     r"(\S+) of the \S+ examples that ship a `requirements.txt`",
     "comment-only requirements files"),
    ("CONTRIBUTING.md", "reqs",
     r"\S+ of the (\S+) examples that ship a `requirements.txt`",
     "examples shipping requirements.txt"),
    ("ROADMAP.md", "plan_tasks", r"\| Enhancement plan \| (\d+) tasks", "enhancement plan tasks"),
    ("ROADMAP.md", "examples", r"\| Examples \| (\d+),", "examples"),
    ("ROADMAP.md", "diagrams", r"\| Diagrams \| (\d+) interactive", "diagrams"),
]


def main(root):
    root = pathlib.Path(root).resolve()
    have = counts(root)
    failures = []

    for filename, key, pattern, about in CLAIMS:
        text = (root / filename).read_text()
        m = re.search(pattern, text)
        if not m:
            failures.append(f"{filename}: the sentence about {about} no longer matches its "
                            f"pattern -- reword the check in docs_counts.py, or the sentence")
            continue
        claimed = to_int(m.group(1))
        if claimed is None:
            failures.append(f"{filename}: could not read {m.group(1)!r} as a number ({about})")
        elif claimed != have[key]:
            line = text[: m.start()].count("\n") + 1
            failures.append(f"{filename}:{line}: claims {m.group(1)} {about}, tree has {have[key]}")

    if failures:
        print("Documentation counts do not match the tree:\n")
        for f in failures:
            print(f"  {f}")
        return 1

    summary = ", ".join(f"{v} {k}" for k, v in sorted(have.items()))
    print(f"{len(CLAIMS)} documented counts checked; all match ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
