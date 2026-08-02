RAG + FAISS Example

A minimal retrieval-augmented generation (RAG) example using `sentence-transformers` and `faiss`.

Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Build index and query

```bash
python build_index.py
python query.py "reproducibility in enterprise ai"
```

Notes

- This example is intentionally small to lower the barrier for experimentation.
- For production, use a persistent vector store (Milvus, Weaviate), chunking, metadata, and secure model endpoints.
