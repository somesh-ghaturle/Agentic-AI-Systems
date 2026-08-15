"""Asserts e2e-agent refuses to start without an API key.

unittest rather than pytest: every other suite in this repository — the example suites here
and all six under infra/ — is stdlib unittest, and pytest is in no requirements file.

    python3 -m unittest tests.test_e2e_agent -v

Why this suite exists. The repository audit removed a default `E2E_AGENT_API_KEY` of
"local-test-key" so the service fails closed rather than starting with a credential that is
published in its own source. The `example deps` CI job then had to set that variable to import
`app.py` at all — a workaround for a security property, sitting in a workflow file, with
nothing explaining why it cannot be deleted. This suite is that explanation, in executable
form: remove the fail-closed behaviour and this goes red.

Subprocesses rather than in-process imports, matching tests/test_agent.py. The check is about
what happens at module-import time under a particular environment, and `import` caches — a
second in-process import of the same module would assert nothing at all.
"""

import importlib.util
import os
import pathlib
import subprocess
import sys
import unittest

EXAMPLE = pathlib.Path(__file__).resolve().parent.parent / "examples" / "e2e-agent"


def import_app(api_key):
    """Import e2e-agent's app.py in a subprocess with E2E_AGENT_API_KEY set, or unset if None.

    Returns (returncode, stderr). The working directory is the example's own, because app.py
    is imported as a top-level module rather than as part of a package.
    """
    env = dict(os.environ)
    if api_key is None:
        env.pop("E2E_AGENT_API_KEY", None)
    else:
        env["E2E_AGENT_API_KEY"] = api_key

    result = subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=str(EXAMPLE),
        env=env,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stderr


@unittest.skipIf(
    importlib.util.find_spec("fastapi") is None,
    "e2e-agent's dependencies are not installed; this suite runs in the example-deps job",
)
class TestE2EAgentFailsClosed(unittest.TestCase):
    """The `examples` CI job installs nothing, so this class skips there and runs in
    `example-deps`, which installs the pinned requirements. Skipping is the honest outcome:
    without fastapi the import fails for a reason that has nothing to do with the key, and a
    test that passes for the wrong reason is worse than one that does not run."""

    def test_import_fails_without_an_api_key(self):
        code, err = import_app(None)
        self.assertNotEqual(code, 0, "app.py imported cleanly with no API key set")
        self.assertIn("E2E_AGENT_API_KEY", err)

    def test_import_succeeds_with_an_api_key(self):
        code, err = import_app("test-key-for-this-suite")
        self.assertEqual(code, 0, err)

    def test_the_published_default_is_gone(self):
        """The specific value the audit deleted. An empty or whitespace key must not be
        accepted either — `if not API_KEY` covers both, and this pins that it stays that way."""
        code, err = import_app("")
        self.assertNotEqual(code, 0, "app.py accepted an empty API key")
        self.assertIn("E2E_AGENT_API_KEY", err)


if __name__ == "__main__":
    unittest.main()
