#!/usr/bin/env python3
"""Query FAISS index and optionally call LangChain/OpenAI to generate an answer.

If `OPENAI_API_KEY` is not set, the script prints retrieved documents and a suggested answer template.
"""
import os
from sentence_transformers import SentenceTransformer
import faiss

DOCS = [
    "Agentic AI systems coordinate tools and models to solve multi-step tasks.",
    "Reproducibility and governance are critical for enterprise deployments.",
    "Use retrieval augmentation to ground model outputs in trusted sources.",
]


def retrieve(q: str, k: int = 2, model_name: str = "all-MiniLM-L6-v2"):
    from pathlib import Path

    model = SentenceTransformer(model_name)
    emb = model.encode([q], convert_to_numpy=True)
    index_path = Path(__file__).resolve().parent / "index.faiss"
    index = faiss.read_index(str(index_path))
    D, I = index.search(emb, k)
    results = [(DOCS[i], float(D[0][j])) for j, i in enumerate(I[0])]
    return results


def answer_with_llm(query: str, context_texts: list[str]):
    try:
        from langchain import LLMChain, PromptTemplate
        from langchain.llms import OpenAI
    except Exception:
        return None
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    llm = OpenAI(temperature=0.0)
    prompt_template = """
You are an assistant. Use the following context to answer the user.

Context:\n{context}\n
User question:\n{question}
"""
    prompt = PromptTemplate(input_variables=["context", "question"], template=prompt_template)
    chain = LLMChain(llm=llm, prompt=prompt)
    out = chain.run({"context": "\n".join(context_texts), "question": query})
    return out.strip()


if __name__ == "__main__":
    import sys
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
