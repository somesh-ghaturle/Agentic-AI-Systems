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
