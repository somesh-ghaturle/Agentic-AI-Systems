RAG + LangChain Example

This example builds a small FAISS index and optionally uses LangChain/OpenAI to answer queries using retrieved context.

Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Build and run

```bash
python build_index.py
python query_and_answer.py "governance needs for enterprise ai"
```

Docker Compose (local test)

```bash
# Edit docker-compose.yml to add your OPENAI_API_KEY if you want LLM answers
cd examples/rag-langchain
docker compose up --build
```

Notes

- The script will not call OpenAI unless `OPENAI_API_KEY` is set. CI can run the example safely without secrets.
- For production, replace FAISS with a managed vector DB and add metadata for provenance.

## Tests

[`tests/test_rag_langchain.py`](../../tests/test_rag_langchain.py) has 5 tests and runs with no
package, model download or key. `faiss`, `sentence_transformers` and LangChain are replaced
with fakes that return chosen vectors and indices. The tests cover index positions mapping back
to documents, the fallback reporting why it fell back, and `DOCS` being one list and not a copy.
Three mutations were each caught: copying `DOCS` again, mapping results by rank instead of by
index, and dropping the no-key message.

## What this is not

Not grounded answering. Without a key, the fallback prints a fixed sentence about governance
whatever the question was -- a template, not a summary of what was retrieved. With a key, the
retrieved text goes into the system prompt unmarked, so a document that contains instructions
is read as instructions: retrieval is an injection path, and this example does nothing about it.

`query_and_answer.py` once kept its own copy of `DOCS`, the bug `rag-faiss` had already fixed;
it now imports the list the index is built from.

## Security

This example makes no security claim, which is why `SECURITY.md` lists it out of scope. The
read/write boundary this repository is organised around is demonstrated by `hermes-agent` and
`graph-agent`; nothing here enforces one, and none of this would be adequate as a production
service as written.
