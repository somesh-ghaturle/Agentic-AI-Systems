#!/usr/bin/env python3
"""Query FAISS index and optionally call LangChain/OpenAI to generate an answer.

If `OPENAI_API_KEY` is not set, the script prints retrieved documents and a suggested answer template.
"""
import os
import sys

import faiss
from sentence_transformers import SentenceTransformer

DOCS = [
    "Agentic AI systems coordinate tools and models to solve multi-step tasks.",
    "Reproducibility and governance are critical for enterprise deployments.",
    "Use retrieval augmentation to ground model outputs in trusted sources.",
]


def retrieve(q: str, k: int = 2, model_name: str = "all-MiniLM-L6-v2"):
    from pathlib import Path  # noqa: PLC0415

    model = SentenceTransformer(model_name)
    emb = model.encode([q], convert_to_numpy=True)
    index_path = Path(__file__).resolve().parent / "index.faiss"
    index = faiss.read_index(str(index_path))
    distances, indices = index.search(emb, k)
    results = [(DOCS[i], float(distances[0][j])) for j, i in enumerate(indices[0])]
    return results


SYSTEM_PROMPT = "You are an assistant. Use the following context to answer the user."


def answer_with_llm(query: str, context_texts: list[str]):
    """Return the model's answer, or None so the caller falls back to the template.

    The reason for returning None goes to stderr rather than staying silent. This function
    previously swallowed every failure — including a version mismatch — into a bare `return
    None`, so the script printed the fallback template and gave no clue why.
    """
    # ImportError only: a bare `except Exception` here hid genuine runtime failures behind
    # the same silent fallback as a missing package.
    try:
        from langchain_core.output_parsers import StrOutputParser  # noqa: PLC0415
        from langchain_core.prompts import ChatPromptTemplate  # noqa: PLC0415
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
    except ImportError as error:
        print(
            f"LangChain is not installed or is a version this example does not target: "
            f"{error}. Install the pinned requirements.txt.",
            file=sys.stderr,
        )
        return None

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set — set it to use the OpenAI model.", file=sys.stderr)
        return None

    template = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT + "\n\nContext:\n{context}"),
            ("human", "{question}"),
        ]
    )
    # LCEL: the pipe replaces LLMChain, which the 1.x line removed outright.
    chain = template | ChatOpenAI(temperature=0.0) | StrOutputParser()
    out = chain.invoke({"context": "\n".join(context_texts), "question": query})
    return out.strip()


if __name__ == "__main__":
    q = "What are governance needs for enterprise AI?" if len(sys.argv) == 1 else " ".join(sys.argv[1:])
    res = retrieve(q)
    print("Retrieved documents:")
    for doc, score in res:
        print(f"- {doc} (score={score:.4f})")
    llm_out = answer_with_llm(q, [r[0] for r in res])
    if llm_out:
        print('\nLLM answer:\n', llm_out)
    else:
        print('\nLLM not available — suggested answer template:\n')
        print('Based on the retrieved sources, the governance needs include inventory, monitoring, retraining triggers, clear ownership, and auditability.')
