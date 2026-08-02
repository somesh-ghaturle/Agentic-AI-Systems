#!/usr/bin/env python3
"""Build a tiny FAISS index from local documents using sentence-transformers.

Requirements: pip install -r requirements.txt
"""
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss

DOCS = [
    "Agentic AI systems coordinate tools and models to solve multi-step tasks.",
    "Reproducibility and governance are critical for enterprise deployments.",
    "FAISS provides efficient similarity search over dense vectors.",
]


def build_index(model_name: str = "all-mpnet-base-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(DOCS, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    faiss.write_index(index, "examples/rag-faiss/index.faiss")
    print(f"Built index with {index.ntotal} vectors (dim={dim})")


if __name__ == "__main__":
    build_index()
