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
