"""Tests ray-orchestrator's fan-out and gather against a real local Ray.

    python3 -m unittest tests.test_ray_orchestrator -v

Skips unless `ray` is installed, so it runs in the `example-deps` CI job and stays out of the
dependency-free one, like tests/test_rag_faiss.py. There is no fake-Ray variant. The example is
eight calls to `remote` and one to `get`, so a fake would test only itself.

What is checked is the two things the example claims: results come back in input order,
whatever order the tasks finish in, and the tasks run in parallel rather than one after another.
The parallel check is deliberately loose. Eight 0.5s tasks run serially take 4s; the bound is
3.5s, which any machine with two or more cores meets with room to spare.
"""

import contextlib
import importlib.util
import io
import pathlib
import time
import unittest

EXAMPLE = pathlib.Path(__file__).resolve().parent.parent / "examples" / "ray-orchestrator"
HAS_RAY = importlib.util.find_spec("ray") is not None


def load():
    spec = importlib.util.spec_from_file_location("ray_orchestrator", EXAMPLE / "orchestrator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAS_RAY, "ray not installed; runs in the example-deps job")
class TestFanOutAndGather(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import ray  # noqa: PLC0415

        cls.ray = ray
        cls.orchestrator = load()
        ray.init(ignore_reinit_error=True, include_dashboard=False, log_to_driver=False)

    @classmethod
    def tearDownClass(cls):
        cls.ray.shutdown()

    def test_results_come_back_in_input_order(self):
        inputs = [8, 3, 5, 1, 7, 2, 6, 4]
        futures = [self.orchestrator.work.remote(x) for x in inputs]
        self.assertEqual(self.ray.get(futures), [x * x for x in inputs])

    def test_the_tasks_run_in_parallel(self):
        start = time.monotonic()
        self.ray.get([self.orchestrator.work.remote(x) for x in range(8)])
        self.assertLess(time.monotonic() - start, 3.5, "eight 0.5s tasks ran close to serially")

    def test_main_prints_the_squares(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.orchestrator.main()
        self.assertIn("Results: [1, 4, 9, 16, 25, 36, 49, 64]", out.getvalue())


if __name__ == "__main__":
    unittest.main()
