#!/usr/bin/env python3
"""Query the example FAISS index.

Run `build_index.py` first to create `index.faiss`.
"""
import faiss

# Imported rather than copied. This list used to be duplicated verbatim in both files, which
# is a silent-corruption bug waiting to happen: the index is built from build_index.DOCS and
# the search results are mapped back to labels by position. Edit one list and the other keeps
# reporting the old text against the new vectors — every result confidently wrong, nothing
# raised, and the two files still looking correct read on their own.
from build_index import DOCS
from sentence_transformers import SentenceTransformer


def query(q: str, k: int = 2, model_name: str = "all-MiniLM-L6-v2"):
    from pathlib import Path  # noqa: PLC0415

    model = SentenceTransformer(model_name)
    emb = model.encode([q], convert_to_numpy=True)
    index_path = Path(__file__).resolve().parent / "index.faiss"
    index = faiss.read_index(str(index_path))
    distances, indices = index.search(emb, k)
    results = [(DOCS[i], float(distances[0][j])) for j, i in enumerate(indices[0])]
    return results


if __name__ == "__main__":
    import sys
    q = "reproducibility in enterprise ai" if len(sys.argv) == 1 else " ".join(sys.argv[1:])
    res = query(q)
    for doc, dist in res:
        print(f"Score: {dist:.4f}\n{doc}\n---")
