"""Run the commands QUICKSTART.md shows with an expected output, and compare.

    python3 -m unittest tests.test_quickstart -v

QUICKSTART.md is the first file a new reader runs, and nothing ran it. By task 79 its hermes
outputs showed a status the agent no longer prints, its trace-eval "expected output" described
100 runs that never existed, and a deploy step called an API Gateway the AWS tree does not
have. This checks the part that can be checked offline: each local command followed by an
**Expected output** block is run, and every line of that block must appear in what it prints.
The trace line is exempt because its ID is random, and so is an elided `...` line.
"""

import pathlib
import re
import shlex
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUICKSTART = (ROOT / "QUICKSTART.md").read_text()

# A ```bash block holding one `python3 examples/...` command, then **Expected output**, then a
# plain ``` block. The deploy steps have no such pairing, and they need a cloud anyway.
# Prose may sit between the two, as it does for trace-eval, but another ```bash block may not.
PAIR = re.compile(
    r"```bash\n(?:#[^\n]*\n)*(python3 examples/[^\n]+)\n```"
    r"(?:(?!```bash).)*?"
    r"\*\*Expected output:?\*\*[^\n]*\n```\n(.*?)```",
    re.S,
)


def documented():
    return [(cmd, block) for cmd, block in PAIR.findall(QUICKSTART)]


class TestQuickstartOutputs(unittest.TestCase):
    def test_the_pairs_are_found(self):
        """If the regex stops matching, this suite checks nothing -- so that is a failure."""
        self.assertGreaterEqual(len(documented()), 3)

    def test_each_documented_line_is_printed(self):
        for cmd, block in documented():
            with self.subTest(cmd=cmd):
                argv = shlex.split(cmd)
                result = subprocess.run(
                    [sys.executable, *argv[1:]],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    stdin=subprocess.DEVNULL,
                )
                for line in block.splitlines():
                    line = line.rstrip()
                    if not line or line.startswith("trace ") or line.strip() == "...":
                        continue
                    self.assertIn(line, result.stdout, f"{cmd}: documented line not printed")


if __name__ == "__main__":
    unittest.main()
