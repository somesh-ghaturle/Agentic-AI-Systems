#!/usr/bin/env python3
"""Query the example FAISS index.

Run `build_index.py` first to create `index.faiss`.
"""
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

DOCS = [
    "Agentic AI systems coordinate tools and models to solve multi-step tasks.",
    "Reproducibility and governance are critical for enterprise deployments.",
    "FAISS provides efficient similarity search over dense vectors.",
]


def query(q: str, k: int = 2, model_name: str = "all-MiniLM-L6-v2"):
    from pathlib import Path

    model = SentenceTransformer(model_name)
    emb = model.encode([q], convert_to_numpy=True)
    index_path = Path(__file__).resolve().parent / "index.faiss"
    index = faiss.read_index(str(index_path))
    D, I = index.search(emb, k)
    results = [(DOCS[i], float(D[0][j])) for j, i in enumerate(I[0])]
    return results


if __name__ == "__main__":
    import sys
    q = "reproducibility in enterprise ai" if len(sys.argv) == 1 else " ".join(sys.argv[1:])
    res = query(q)
    for doc, dist in res:
        print(f"Score: {dist:.4f}\n{doc}\n---")
