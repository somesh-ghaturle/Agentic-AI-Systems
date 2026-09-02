#!/usr/bin/env python3
"""Check every third-party module an example imports is pinned in its requirements.txt.

    python3 .github/scripts/example_deps.py examples

Exits non-zero, naming example, module, and the file that imports it, if any example imports
something it does not declare.

Two graphs, because there are two things worth knowing and they have different shapes.

**Example to distribution**, which cannot cycle — packages have no edges back out — and which
is where the real breakage lives. It fired on the first run: `graph-agent` imported
`typing_extensions` while pinning only `langgraph`. It worked, because langgraph pulls
typing-extensions in transitively, which is exactly what makes it worth catching. The example
was one upstream dependency change away from breaking for anyone who installed it from its own
requirements file, and nothing in CI would have noticed, because CI installed the same
transitive tree.

**Example to example**, which can. `trace-eval` evaluates `hermes-agent` by putting the
sibling directory on `sys.path` and importing `hermes` from it, so the examples are not
independent and a cycle between them is constructible. One exists today, it runs in that
direction only, and nothing but this check would stop someone adding the return edge. Cycle
detection here is an eleven-line depth-first search over a graph with thirteen nodes, which is
why this file has no third-party dependency of its own.

Standard library only, like every other check here, and worth stating because the plan this
task came from specified `networkx` for the cycle check — over the example-to-package graph,
where a cycle is unconstructible. The goal was right and the graph was the wrong one.

Five things a naive implementation gets wrong. All five were established by writing one.

**Local sibling modules.** `from harness import ...`, `from debate import ...`, and
`from build_index import ...` are files sitting next to the importing module, not packages.
Grepping for imports flags all of them. Anything resolving to a `.py` file or package
directory inside the same example is local and skipped.

**Cross-example imports look exactly like missing dependencies.** `from hermes import Tracer`
in trace-eval names no distribution and no local file, so the first version of this check
reported it as an unpinned dependency. It resolves inside `examples/hermes-agent`, which makes
it an edge in the second graph rather than a fault in the first.

**Import name is not distribution name.** `import faiss` is satisfied by `faiss-cpu`.
PEP 503 normalisation (lowercase, runs of `-_.` collapsed to `-`) handles most of the gap on
its own — `typing_extensions` to `typing-extensions`, `langchain_core` to `langchain-core` —
so only genuinely irregular names need the alias table below, which keeps it short enough to
stay correct.

**Namespace packages.** `opentelemetry.sdk.trace` and `opentelemetry.trace` are one top-level
import satisfied by either of two distributions. The check resolves to the top-level name and
accepts any one of the mapped distributions.

**Requirements syntax.** `uvicorn[standard]==0.52.3` declares `uvicorn`. Extras, version
specifiers, comments, and blank lines all have to come off before comparing.

The unused direction — pinned but never imported — is reported, not enforced. Every current
instance is deliberate: `uvicorn` is the server entrypoint invoked from the Dockerfile rather
than imported, and `numpy` is pinned to constrain a transitive dependency that would otherwise
float. A check that failed on those would be wrong, and a check that is right about a narrow
thing beats one that is approximately right about a wide one.
"""

import ast
import pathlib
import sys

# Import name -> distributions that satisfy it. Only irregular cases belong here; anything
# that differs from its distribution by case or by `_` versus `-` is handled by normalise().
ALIASES = {
    "faiss": {"faiss-cpu", "faiss-gpu"},
    "opentelemetry": {"opentelemetry-api", "opentelemetry-sdk"},
}


def normalise(name):
    """PEP 503 name normalisation, so `typing_extensions` matches `typing-extensions`."""
    out = []
    for char in name.lower():
        out.append("-" if char in "-_." else char)
    while "--" in (joined := "".join(out)):
        out = list(joined.replace("--", "-"))
    return "".join(out)


def declared(requirements):
    """Distribution names pinned in a requirements.txt, normalised.

    Strips comments, extras, and version specifiers: `uvicorn[standard]==0.52.3` -> `uvicorn`.
    """
    if not requirements.exists():
        return set()
    names = set()
    for line in requirements.read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        for delimiter in ("[", "==", ">=", "<=", "~=", "!=", ">", "<", ";"):
            line = line.split(delimiter, 1)[0]
        if line.strip():
            names.add(normalise(line.strip()))
    return names


def imported(example):
    """Top-level modules imported by an example, as {module: [files that import it]}.

    Uses ast rather than a regex so that imports inside try/except and inside functions are
    found — graph-agent's langgraph import is guarded, and is the one that matters most.
    """
    found = {}
    for path in sorted(example.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(), filename=str(path))
        except SyntaxError as exc:  # a broken example is the syntax job's problem, not ours
            print(f"  ! {path}: {exc}", file=sys.stderr)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                # level > 0 is an explicit relative import, always local.
                names = [node.module] if node.module and node.level == 0 else []
            else:
                continue
            for name in names:
                found.setdefault(name.split(".")[0], []).append(path)
    return found


def resolves_in(module, directory):
    """Does this module name resolve to a file or package inside this directory?"""
    return (directory / f"{module}.py").exists() or (
        directory / module / "__init__.py"
    ).exists()


def is_local(module, example):
    """A `.py` file or package directory sitting inside the example is not a dependency."""
    return resolves_in(module, example)


def owning_example(module, root, importer):
    """The *other* example this module lives in, if any.

    trace-eval reaches hermes-agent by putting the sibling directory on sys.path. That is a
    real edge between examples, not a missing pin.
    """
    for candidate in sorted(p for p in root.iterdir() if p.is_dir()):
        if candidate == importer or candidate.name.startswith("."):
            continue
        if resolves_in(module, candidate):
            return candidate.name
    return None


def find_cycle(edges):
    """Depth-first search for a cycle in the example-to-example graph.

    Returns the cycle as a list of names, or None. Iterative rather than recursive for no
    reason beyond keeping the stack legible in a failure message.
    """
    WHITE, GREY, BLACK = 0, 1, 2
    colour = dict.fromkeys(edges, WHITE)

    for start in sorted(edges):
        if colour[start] != WHITE:
            continue
        stack = [(start, iter(sorted(edges[start])))]
        path = [start]
        colour[start] = GREY
        while stack:
            node, children = stack[-1]
            for child in children:
                if colour.get(child, WHITE) == GREY:
                    return [*path[path.index(child):], child]
                if colour.get(child, WHITE) == WHITE:
                    colour[child] = GREY
                    path.append(child)
                    stack.append((child, iter(sorted(edges.get(child, ())))))
                    break
            else:
                colour[node] = BLACK
                stack.pop()
                path.pop()
    return None


def satisfied_by(module, pins):
    """Is this import covered by the pinned distributions?"""
    if normalise(module) in pins:
        return True
    return bool(ALIASES.get(module, set()) & pins)


def check(root):
    stdlib = sys.stdlib_module_names
    failures = []
    unused = []
    edges = {}

    examples = [
        p
        for p in sorted(root.iterdir())
        if p.is_dir() and not p.name.startswith(".") and p.name != "__pycache__"
    ]
    for example in examples:
        edges.setdefault(example.name, set())
        pins = set()
        for req in sorted(example.rglob("requirements.txt")):
            if "__pycache__" in req.parts:
                continue
            pins |= declared(req)
        modules = imported(example)

        third_party = set()
        for module, files in sorted(modules.items()):
            if module in stdlib or module == "__future__" or is_local(module, example):
                continue
            owner = owning_example(module, root, example)
            if owner:
                edges[example.name].add(owner)
                continue
            third_party.add(normalise(module))
            if not satisfied_by(module, pins):
                where = ", ".join(str(f.relative_to(root.parent)) for f in sorted(set(files)))
                failures.append((example.name, module, where))

        print(f"  {example.name}: {', '.join(sorted(pins)) or 'no dependencies'}")

        for pin in sorted(pins):
            aliased = any(pin in ALIASES.get(m, set()) for m in modules)
            if pin not in third_party and not aliased:
                unused.append((example.name, pin))

    if unused:
        print("\nPinned but not imported (informational — entrypoints and transitive pins):")
        for name, pin in unused:
            print(f"  {name}: {pin}")

    between = {a: b for a, b in edges.items() if b}
    if between:
        print("\nBetween examples:")
        for name, targets in sorted(between.items()):
            print(f"  {name} -> {', '.join(sorted(targets))}")

    cycle = find_cycle(edges)
    if cycle:
        print(
            "\nERROR: circular dependency between examples: " + " -> ".join(cycle),
            file=sys.stderr,
        )
        print(
            "Examples must stay independently runnable. Break the cycle by copying what is "
            "shared, or by moving it somewhere both can import.",
            file=sys.stderr,
        )
        return 1

    if failures:
        print("\nERROR: imported but not pinned:", file=sys.stderr)
        for name, module, where in failures:
            print(f"  {name}: {module} (imported by {where})", file=sys.stderr)
        print(
            "\nAdd it to that example's requirements.txt. It may work today by arriving as a "
            "transitive dependency, which is the problem — that is not a guarantee.",
            file=sys.stderr,
        )
        return 1

    print("\nEvery imported module is pinned. No cycles between examples.")
    return 0


def main(argv):
    root = pathlib.Path(argv[1] if len(argv) > 1 else "examples")
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    print(f"Example dependencies under {root}:")
    return check(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
