"""Tests langchain-agent's three paths: no package, no key, and the chain itself.

    python3 -m unittest tests.test_langchain_agent -v

Runs in the dependency-free `examples` job. The LangChain modules are replaced in
`sys.modules` with small fakes, so no package, key or network is needed. The fakes check only
what this example does: it builds `template | model | parser` and invokes it with the prompt.
They do not pretend to test LangChain.

What is worth pinning is the error handling. The comments in agent.py record two earlier
versions that hid failures: a bare `except Exception` reported "not installed" for a version
mismatch, and a silent fallback hid auth failures behind the word "fallback".
"""

import contextlib
import importlib.util
import io
import os
import pathlib
import sys
import types
import unittest
from unittest import mock

AGENT = pathlib.Path(__file__).resolve().parent.parent / "examples" / "langchain-agent" / "agent.py"
LANGCHAIN = ("langchain_core.output_parsers", "langchain_core.prompts", "langchain_openai")


def load():
    # A unique module name: three examples ship an agent.py, and a bare `import agent` binds
    # whichever one the run imported first (task 54).
    spec = importlib.util.spec_from_file_location("langchain_agent_under_test", AGENT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Pipe:
    """Enough of LCEL's `|` to record what was composed, and what it was invoked with."""

    def __init__(self, parts):
        self.parts = parts
        self.invoked_with = None

    def __or__(self, other):
        return _Pipe([*self.parts, other])

    def invoke(self, value):
        self.invoked_with = value
        _Pipe.last = self
        return "  a concise answer  "


def fake_langchain(calls):
    template = types.SimpleNamespace(from_messages=lambda msgs: _Pipe([("template", msgs)]))

    def chat(**kwargs):
        calls.append(kwargs)
        return ("model", kwargs)

    return {
        "langchain_core": types.ModuleType("langchain_core"),
        "langchain_core.output_parsers": types.SimpleNamespace(StrOutputParser=lambda: "parser"),
        "langchain_core.prompts": types.SimpleNamespace(ChatPromptTemplate=template),
        "langchain_openai": types.SimpleNamespace(ChatOpenAI=chat),
    }


class TestWithoutTheDependencies(unittest.TestCase):
    def test_a_missing_package_says_install_the_requirements(self):
        blocked = dict.fromkeys(LANGCHAIN)  # None in sys.modules makes the import raise
        with mock.patch.dict(sys.modules, blocked):
            out = load().run_with_langchain("hello")
        self.assertIn("not installed", out)
        self.assertIn("requirements.txt", out)

    def test_a_broken_install_is_not_reported_as_a_missing_one(self):
        """Only ImportError means "not installed". A package that is present but fails in
        some other way must surface as itself, or people reinstall a correct package."""

        class Broken(types.ModuleType):
            def __getattr__(self, name):
                raise RuntimeError("incompatible langchain_core build")

        modules = fake_langchain([])
        modules["langchain_core.output_parsers"] = Broken("langchain_core.output_parsers")
        with mock.patch.dict(sys.modules, modules), self.assertRaises(RuntimeError):
            load().run_with_langchain("hello")

    def test_a_missing_key_stops_before_any_model_is_built(self):
        calls = []
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with mock.patch.dict(sys.modules, fake_langchain(calls)), \
                mock.patch.dict(os.environ, env, clear=True):
            out = load().run_with_langchain("hello")
        self.assertIn("OPENAI_API_KEY not set", out)
        self.assertEqual(calls, [], "a model client was built with no key")


class TestTheChain(unittest.TestCase):
    def test_it_composes_template_model_parser_and_invokes_with_the_prompt(self):
        calls = []
        with mock.patch.dict(sys.modules, fake_langchain(calls)), \
                mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            out = load().run_with_langchain("summarize this")
        self.assertEqual(out, "a concise answer", "the answer should be stripped")
        pipe = _Pipe.last
        self.assertEqual([p if isinstance(p, str) else p[0] for p in pipe.parts],
                         ["template", "model", "parser"])
        self.assertEqual(pipe.invoked_with, {"input": "summarize this"})
        self.assertEqual(calls, [{"temperature": 0.2}])


class TestTheFallbackNamesTheError(unittest.TestCase):
    def test_an_unexpected_failure_is_printed_not_swallowed(self):
        module = load()
        with mock.patch.object(module, "run_with_langchain", side_effect=RuntimeError("401")), \
                mock.patch.object(sys, "argv", ["agent.py", "hello"]), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            module.main()
        self.assertIn("fallback after RuntimeError: 401", out.getvalue())


if __name__ == "__main__":
    unittest.main()
