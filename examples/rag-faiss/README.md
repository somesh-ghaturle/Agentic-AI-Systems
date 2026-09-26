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

## What this is not

Not a retrieval pipeline. Three hard-coded sentences, no chunking, no metadata, no provenance,
and no generation step. The printed `Score` is a squared L2 distance, so lower is closer -- the
opposite of what the label suggests. The index is rebuilt from scratch on every
`build_index.py`, and nothing checks that it was built with the same model `query.py` loads.

## Security

This example makes no security claim, which is why `SECURITY.md` lists it out of scope. The
read/write boundary this repository is organised around is demonstrated by `hermes-agent` and
`graph-agent`; nothing here enforces one, and none of this would be adequate as a production
service as written.
