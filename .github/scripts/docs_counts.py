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
number. Digits, unit words, tens words and hyphenated compounds up to ninety-nine are all
understood, because this repository writes small numbers as words in prose and as digits in
tables. A claim whose regex stops matching is a failure, not a skip: rewording the sentence is
exactly when the number needs looking at again.

Three different numbers describe the Terraform trees on purpose, and conflating them is the
mistake this guards. `validate` skips the hybrid POC (13 roots); tflint walks every module and
root including it (44 and 14); the write-boundary suites cover the four non-hybrid trees.

Standard library only, like every other check here.
"""

import pathlib
import re
import sys

_UNITS = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen",
)
UNITS = {w: i for i, w in enumerate(_UNITS)}
TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}


def to_int(token):
    """Digits, a unit word, a tens word, or a hyphenated compound like "forty-four"."""
    token = token.strip().lower().strip(".,;:")
    if token.isdigit():
        return int(token)
    if token in UNITS:
        return UNITS[token]
    if token in TENS:
        return TENS[token]
    if "-" in token:
        tens, _, unit = token.partition("-")
        if tens in TENS and unit in UNITS and 0 < UNITS[unit] < 10:
            return TENS[tens] + UNITS[unit]
    return None


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

    # Infrastructure shape. `validate` deliberately skips the hybrid POC, while tflint walks
    # every module and root including it, so these are three different numbers on purpose.
    checks_text = (root / ".github/workflows/checks.yml").read_text()
    validate_block = re.search(r"^  validate:.*?^    steps:", checks_text, re.S | re.M)
    validate_roots = len(re.findall(r"^\s+- infra/", validate_block.group(0), re.M))
    matrix_trees = re.findall(r"^        tree: \[([^\]]+)\]", checks_text, re.M)
    boundary_trees = len(re.findall(r"unittest discover -s infra/terraform-[a-z]+/tests",
                                    checks_text))

    return {
        "examples": len(examples),
        "suites": len(suites),
        "reqs": len(reqs),
        "stdlib_only": len(stdlib_only),
        "jobs": jobs,
        "deps_legs": deps_legs,
        "plan_tasks": plan_tasks,
        "diagrams": len(list((root / "docs/diagrams").glob("*.html"))),
        "validate_roots": validate_roots,
        "tf_modules": len([d for d in root.glob("infra/terraform-*/modules/*") if d.is_dir()]),
        "tf_env_roots": len([d for d in root.glob("infra/terraform-*/envs/*") if d.is_dir()]),
        "tf_trees": len([d for d in root.glob("infra/terraform-*") if d.is_dir()]),
        "handler_trees": len(matrix_trees[0].split(",")) if matrix_trees else 0,
        "package_trees": len(matrix_trees[1].split(",")) if len(matrix_trees) > 1 else 0,
        "boundary_trees": boundary_trees,
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
    ("ROADMAP.md", "tf_trees", r"\| Terraform trees \| (\d+) —", "terraform trees"),
    ("README.md", "validate_roots", r"`terraform validate` on each of the (\S+) environment roots",
     "environment roots in the validate matrix"),
    ("README.md", "tf_modules", r"`tflint` over all (\S+) modules", "terraform modules"),
    ("README.md", "tf_env_roots", r"`tflint` over all \S+ modules and (\S+) roots",
     "env roots tflint walks"),
    ("README.md", "boundary_trees", r"Write-boundary tests for all (\S+) trees",
     "trees with write-boundary suites"),
    ("README.md", "handler_trees", r"Handler logic tests for the (\S+) trees that have handlers",
     "trees with handlers"),
    ("README.md", "package_trees", r"Deployment package builds for the (\S+) trees that have",
     "trees with packages"),
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
