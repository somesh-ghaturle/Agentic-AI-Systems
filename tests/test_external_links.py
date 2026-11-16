"""Tests the weekly external-link report, without touching the network.

    python3 -m unittest tests.test_external_links -v

Two things are pinned: which links it picks up, and which answers it treats as dead. The second
is the one that matters. A report that calls a 403 dead is a report nobody reads twice.
"""

import importlib.util
import pathlib
import socket
import unittest
import urllib.error
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "external_links.py"

_spec = importlib.util.spec_from_file_location("external_links", SCRIPT)
external_links = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(external_links)


def _http(code):
    return urllib.error.HTTPError("https://x.test", code, "", None, None)


class ExternalLinksTest(unittest.TestCase):
    def test_finds_external_links_and_skips_fences_and_relative_ones(self):
        text = "[a](https://a.test/p#frag) [b](docs/b.md)\n```\n[c](https://c.test)\n```\n"
        self.assertEqual(list(external_links.external_links(text)), [(1, "https://a.test/p")])

    def test_only_a_definite_answer_is_dead(self):
        cases = [
            (_http(404), "HTTP 404"),
            (_http(410), "HTTP 410"),
            (_http(403), None),
            (_http(429), None),
            (urllib.error.URLError(socket.gaierror()), "host does not resolve"),
            (urllib.error.URLError(socket.timeout()), None),
        ]
        for error, expected in cases:
            with mock.patch("urllib.request.urlopen", side_effect=error):
                self.assertEqual(external_links.verdict("https://x.test"), expected, error)


if __name__ == "__main__":
    unittest.main()
