"""Tests rag-langchain's retrieval mapping, its no-key fallback, and the drift bug it had.

    python3 -m unittest tests.test_rag_langchain -v

Runs in the dependency-free `examples` job. `faiss`, `sentence_transformers` and the LangChain
modules are replaced in `sys.modules` with fakes, so no package, model download, key or network
is needed. The fakes return chosen vectors and indices, and every assertion is about what this
example does with them: map index positions back to documents, and decline to call a model it
cannot reach.

**Why the modules are loaded under unique names.** rag-faiss also ships a `build_index.py`. In
one test run, a bare `import build_index` binds whichever of the two was imported first. That
is the task 54 bug, and here it would make the DOCS identity test compare the wrong lists.
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

EXAMPLE = pathlib.Path(__file__).resolve().parent.parent / "examples" / "rag-langchain"


class _Index:
    def __init__(self, distances, indices):
        self.result = (distances, indices)

    def search(self, emb, k):
        return self.result


def fakes(index=None):
    model = types.SimpleNamespace(encode=lambda texts, convert_to_numpy: [[0.0] * 3])
    return {
        "faiss": types.SimpleNamespace(read_index=lambda path: index),
        "sentence_transformers": types.SimpleNamespace(SentenceTransformer=lambda name: model),
    }


def load(stubs):
    """Load this example's build_index and query_and_answer, isolated from rag-faiss's."""
    with mock.patch.dict(sys.modules, stubs):
        mods = {}
        for name in ("build_index", "query_and_answer"):
            spec = importlib.util.spec_from_file_location(
                f"rag_langchain_{name}", EXAMPLE / f"{name}.py"
            )
            mod = importlib.util.module_from_spec(spec)
            # query_and_answer does `from build_index import DOCS`; make that this example's.
            sys.modules["build_index"] = mods.get("build_index", mod)
            spec.loader.exec_module(mod)
            mods[name] = mod
        return mods["build_index"], mods["query_and_answer"]


class TestTheDriftBug(unittest.TestCase):
    """query_and_answer.py once kept its own copy of DOCS (task 74)."""

    def test_query_does_not_define_its_own_copy(self):
        source = (EXAMPLE / "query_and_answer.py").read_text(encoding="utf-8")
        self.assertNotIn("DOCS = [", source)

    def test_both_modules_see_the_same_list_object(self):
        build_index, qa = load(fakes())
        self.assertIs(qa.DOCS, build_index.DOCS)


class TestRetrieval(unittest.TestCase):
    def test_results_are_mapped_back_to_documents_by_position(self):
        # The stubs are bound at import, so retrieve() uses the index given here.
        _, qa = load(fakes(_Index([[0.1, 0.4]], [[2, 0]])))
        results = qa.retrieve("governance")
        self.assertEqual(results, [(qa.DOCS[2], 0.1), (qa.DOCS[0], 0.4)])


class TestNoModelWithoutWhatItNeeds(unittest.TestCase):
    """Returning None sends the caller to the fallback. The reason must reach stderr."""

    LANGCHAIN = ("langchain_core.output_parsers", "langchain_core.prompts", "langchain_openai")

    def test_a_missing_package_returns_none_and_says_why(self):
        _, qa = load(fakes())
        blocked = dict.fromkeys(self.LANGCHAIN)
        with mock.patch.dict(sys.modules, blocked), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(qa.answer_with_llm("q", ["ctx"]))
        self.assertIn("requirements.txt", err.getvalue())

    def test_a_missing_key_returns_none_and_says_why(self):
        _, qa = load(fakes())
        stub = types.SimpleNamespace(
            StrOutputParser=object, ChatPromptTemplate=object, ChatOpenAI=object
        )
        modules = {"langchain_core": types.ModuleType("langchain_core"),
                   **dict.fromkeys(self.LANGCHAIN, stub)}
        env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
        with mock.patch.dict(sys.modules, modules), \
                mock.patch.dict(os.environ, env, clear=True), \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertIsNone(qa.answer_with_llm("q", ["ctx"]))
        self.assertIn("OPENAI_API_KEY not set", err.getvalue())


if __name__ == "__main__":
    unittest.main()
