"""Run each example the way its README says to, and assert it exits cleanly.

    python3 -m unittest tests.smoke.test_example_smoke -v

This is the only check here that *executes* an example. The `examples` job already runs the
unit suites and `compileall`, and between them they miss a specific thing: `compileall` parses
without importing, so it cannot see a dependency that stopped exporting a name, and the unit
suites import modules rather than running entry points, so they cannot see a `__main__` block
that raises. Both failures reach a user on their first command.

Each example is run as a subprocess from the repository root, with the arguments its own
README documents, and is expected to exit 0 having printed something.

**Why not `--help`.** The task this came from probed every example with `--help` and asserted
`"usage"` appeared. Two of thirteen examples use argparse. The rest ignore unknown flags and
run their demo, so the assertion failed on most of them — and `checkpoint-agent` accepts a
positional action, so `--help` made it dutifully report `Executing: --help`. A smoke test that
has to be argued into passing is not testing anything. Running the documented command is both
simpler and closer to what a user actually does.

**Timeouts are a real case, not defensive padding.** An agent example that waits on input it
will never receive hangs rather than fails, and a hung CI job is worse than a red one — it
burns the runner's full timeout and reports nothing useful. Each subprocess gets a hard limit
and an empty stdin, so anything reading input fails immediately instead of blocking.

**State.** `checkpoint-agent` persists to `state.json` next to its own source, by design — it
is the crash-recovery example. That file is gitignored, so a run does not dirty the tree, but
it does carry between runs, so this suite snapshots and restores it. Without that, running the
suite twice tests something different the second time, and a developer's local state is
collateral.
"""

import importlib.util
import pathlib
import shutil
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXAMPLES = ROOT / "examples"

# (example, script, arguments, expected exit code) — the invocation each README documents.
# Examples needing a model, a key, a server, or a heavyweight dependency are excluded; see
# SKIPPED below.
#
# The exit code is part of the contract, not boilerplate. hermes-agent exits **2** when it
# reaches a write it has not been told to approve, and its README says so — that is the write
# boundary refusing, and a smoke test that demanded 0 everywhere would have recorded the
# repository's central control as a failure. All three hermes rows are here together because
# the interesting assertion is the difference between them.
CASES = [
    ("checkpoint-agent", "agent.py", ["deploy-model"], 0),
    ("context-compaction", "compact.py", [], 0),
    ("harness-agent", "agent.py", ["Find and plan deployment for service X"], 0),
    ("hermes-agent", "agent.py", ["what is the refund policy"], 0),
    ("hermes-agent", "agent.py", ["restart the billing service"], 2),
    ("hermes-agent", "agent.py", ["restart the billing service", "--approve"], 0),
    ("multi-agent-debate", "agent.py", [], 0),
    ("starter-agent", "agent.py", ["what is the refund policy"], 0),
    ("tool-discovery", "discover.py", [], 0),
    ("trace-eval", "eval.py", [], 0),
]

# Requires a third-party package. Runs when it is installed — which is the case in the
# example-deps job — and skips otherwise, the same arrangement tests/test_graph_agent.py uses.
CONDITIONAL = [
    ("graph-agent", "graph_agent.py", [], 0, "langgraph"),
]

# Deliberately not smoke-tested, and why. Left here because "which examples does this cover"
# is the first question anyone reading it will have.
SKIPPED = {
    "e2e-agent": "an HTTP server; it does not exit on its own",
    "langchain-agent": "needs an API key",
    "rag-langchain": "needs an API key",
    "rag-faiss": "builds an index over a Torch model download; too slow for this job",
    "ray-orchestrator": "starts a Ray cluster; too slow for this job",
}

TIMEOUT_SECONDS = 60


def run_example(example, script, args):
    """Run one example from the repository root with stdin closed."""
    return subprocess.run(
        [sys.executable, str(EXAMPLES / example / script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
        stdin=subprocess.DEVNULL,
    )


class ExampleSmokeMixin:
    def assert_runs(self, example, script, args, expected=0):
        try:
            result = run_example(example, script, args)
        except subprocess.TimeoutExpired:
            self.fail(
                f"{example}/{script} did not finish within {TIMEOUT_SECONDS}s. "
                "If it is waiting on input, it should fail rather than block."
            )

        self.assertEqual(
            result.returncode,
            expected,
            f"{example}/{script} {' '.join(args)} exited {result.returncode}, "
            f"expected {expected}\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}",
        )
        self.assertTrue(
            result.stdout.strip(),
            f"{example}/{script} exited 0 but printed nothing, which is not a working demo",
        )
        return result


class TestExamplesRun(ExampleSmokeMixin, unittest.TestCase):
    """Every stdlib-only example, run as documented."""

    def setUp(self):
        # checkpoint-agent writes next to its own source and resumes from it.
        self.state = EXAMPLES / "checkpoint-agent" / "state.json"
        self.saved = self.state.read_bytes() if self.state.exists() else None

    def tearDown(self):
        if self.saved is not None:
            self.state.write_bytes(self.saved)
        elif self.state.exists():
            self.state.unlink()

    def test_examples_run(self):
        for example, script, args, expected in CASES:
            with self.subTest(example=example, args=" ".join(args)):
                self.assert_runs(example, script, args, expected)


class TestConditionalExamples(ExampleSmokeMixin, unittest.TestCase):
    """Examples with a dependency, skipped when it is absent."""

    def test_examples_run(self):
        for example, script, args, expected, requirement in CONDITIONAL:
            with self.subTest(example=example):
                if importlib.util.find_spec(requirement) is None:
                    self.skipTest(f"{requirement} not installed; runs in the example-deps job")
                self.assert_runs(example, script, args, expected)


class TestTheTableItself(unittest.TestCase):
    """The table is the test. If it drifts from the tree, the suite silently covers less."""

    def test_every_example_is_covered_or_explicitly_skipped(self):
        """A new example must be added here or named in SKIPPED, not quietly omitted."""
        on_disk = {p.name for p in EXAMPLES.iterdir() if p.is_dir() and p.name != "__pycache__"}
        accounted = {c[0] for c in CASES} | {c[0] for c in CONDITIONAL} | set(SKIPPED)
        self.assertEqual(
            on_disk - accounted,
            set(),
            "example(s) neither smoke-tested nor listed in SKIPPED with a reason",
        )

    def test_the_table_names_no_example_that_does_not_exist(self):
        on_disk = {p.name for p in EXAMPLES.iterdir() if p.is_dir()}
        for name in {c[0] for c in CASES} | {c[0] for c in CONDITIONAL} | set(SKIPPED):
            self.assertIn(name, on_disk, f"{name} is in the table but not in examples/")

    def test_every_script_named_exists(self):
        for example, script, *_ in [*CASES, *CONDITIONAL]:
            self.assertTrue(
                (EXAMPLES / example / script).is_file(),
                f"{example}/{script} does not exist — the documented entry point moved",
            )

    def test_python_is_available(self):
        self.assertTrue(shutil.which(sys.executable) or pathlib.Path(sys.executable).exists())


if __name__ == "__main__":
    unittest.main()
