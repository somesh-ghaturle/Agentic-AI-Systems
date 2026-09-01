"""Guard against an example becoming catastrophically slower than it is.

    python3 -m unittest tests.performance.test_performance -v

**These are not latency SLOs, and the thresholds are deliberately loose.** Measured on the
development machine, `hermes-agent` takes about 37ms end to end and `graph-agent` about 350ms.
The ceilings here are roughly twenty times that. A test that asserted 40ms would fail whenever
a shared CI runner was busy, get marked flaky, and then get deleted — which is worse than no
test, because the deletion takes the real signal with it.

What twenty-times headroom still catches is the regression that actually threatens these
examples: **something started doing I/O.** A DNS lookup and a TCP connect cost tens to hundreds
of milliseconds even when they succeed, and seconds when they do not. An example that is
stdlib-only and computes in memory cannot drift from 37ms to 800ms by accident; it gets there
by someone adding a network call, a model client, or an accidental O(n²) over the knowledge
base. That is the class this guards, and loose bounds catch it just as well as tight ones.

**Interpreter startup dominates the fast cases**, which is why both numbers are reported.
A bare `python3 -c pass` costs about 13ms on the same machine — over a third of hermes-agent's
wall clock. Measuring only the process would mean a third of the budget belongs to CPython
rather than to the example, and a change in Python version would move the number more than any
plausible code change. So the suite records process wall-clock, which is what a user feels, and
separately the in-process work, which is where a regression in the example itself shows up.

**Median, not mean.** One slow spawn on a contended runner moves a mean of five samples far
more than it moves the median. The maximum is printed but not asserted on, because it is the
sample most contaminated by whatever else the runner was doing.

The measured baselines in `CASES` are recorded so the ceilings can be audited rather than
taken on faith. If an example legitimately gets slower, update the baseline in the same commit
that makes it slower, and the diff will say so.
"""

import importlib.util
import pathlib
import statistics
import subprocess
import sys
import time
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
EXAMPLES = ROOT / "examples"

ITERATIONS = 5

# (name, argv, measured baseline ms, ceiling ms, required module)
# Baselines measured 2026-08-26. Ceilings are ~20x, for the reasons in the docstring.
CASES = [
    ("hermes-agent", ["hermes-agent/agent.py", "--quiet", "test query"], 37, 800, None),
    ("graph-agent", ["graph-agent/graph_agent.py"], 354, 7000, "langgraph"),
]


def timed_run(argv):
    """One subprocess, wall-clock milliseconds."""
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(EXAMPLES / argv[0]), *argv[1:]],
        cwd=ROOT,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        timeout=60,
    )
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, result


def interpreter_baseline():
    """What an empty interpreter costs, so the example's share is legible."""
    samples = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        subprocess.run([sys.executable, "-c", "pass"], capture_output=True)
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.median(samples)


class TestExampleLatency(unittest.TestCase):
    """Each example, run repeatedly, held to a ceiling far above its measured cost."""

    @classmethod
    def setUpClass(cls):
        cls.startup = interpreter_baseline()

    def test_latency(self):
        for name, argv, baseline, ceiling, requirement in CASES:
            with self.subTest(example=name):
                if requirement and importlib.util.find_spec(requirement) is None:
                    self.skipTest(f"{requirement} not installed; runs in the example-deps job")

                samples = []
                for _ in range(ITERATIONS):
                    elapsed, result = timed_run(argv)
                    self.assertEqual(
                        result.returncode,
                        0,
                        f"{name} exited {result.returncode}; timing a failing run is "
                        f"meaningless\n{result.stderr}",
                    )
                    samples.append(elapsed)

                median = statistics.median(samples)
                work = max(median - self.startup, 0.0)
                print(
                    f"\n  {name}: median {median:.0f}ms "
                    f"(≈{work:.0f}ms after {self.startup:.0f}ms interpreter startup), "
                    f"max {max(samples):.0f}ms, baseline {baseline}ms, ceiling {ceiling}ms"
                )

                self.assertLess(
                    median,
                    ceiling,
                    f"{name} median {median:.0f}ms exceeds its {ceiling}ms ceiling "
                    f"(baseline {baseline}ms). This is ~20x headroom, so it does not mean the "
                    f"runner was slow — something is doing work it did not do before, most "
                    f"likely I/O.",
                )


class TestTheBaselinesAreHonest(unittest.TestCase):
    """The table is a claim about the tree. Claims rot."""

    def test_every_case_points_at_a_real_file(self):
        for name, argv, *_ in CASES:
            self.assertTrue(
                (EXAMPLES / argv[0]).is_file(),
                f"{name}: {argv[0]} does not exist — the entry point moved",
            )

    def test_ceilings_leave_real_headroom(self):
        """A ceiling close to its baseline is a flaky test waiting to happen."""
        for name, _, baseline, ceiling, _ in CASES:
            self.assertGreaterEqual(
                ceiling / baseline,
                10,
                f"{name}: ceiling {ceiling}ms is under 10x its {baseline}ms baseline, which "
                "is tight enough to fail on a contended runner",
            )

    def test_arguments_are_accepted_by_the_example(self):
        """hermes-agent's --quiet is load-bearing here: without it the run prints a trace to
        stderr, and an unknown flag would exit 2 and be timed as a failure."""
        _, result = timed_run(["hermes-agent/agent.py", "--quiet", "test query"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "", "--quiet should suppress the trace")


if __name__ == "__main__":
    unittest.main()
