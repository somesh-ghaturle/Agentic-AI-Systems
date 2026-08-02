#!/usr/bin/env python3
"""Minimal LangChain-style agent example.

Requirements: pip install -r requirements.txt

This script will echo the prompt if LangChain/OpenAI isn't available or
if `OPENAI_API_KEY` isn't set. If you have an OpenAI API key, set
`OPENAI_API_KEY` in your environment to run with the real LLM.
"""
import os
import sys

PROMPT = "\n".join(["You are a helpful assistant.", "Answer concisely."])


def run_with_langchain(prompt: str) -> str:
    try:
        from langchain import LLMChain, PromptTemplate
        from langchain.llms import OpenAI
    except Exception:
        return "LangChain or OpenAI not installed — install requirements to run with real LLM."

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "OPENAI_API_KEY not set — set it to use OpenAI LLM."

    llm = OpenAI(temperature=0.2)
    template = PromptTemplate(input_variables=["system", "input"], template="""
{system}

User: {input}
""")
    chain = LLMChain(llm=llm, prompt=template)
    out = chain.run({"system": PROMPT, "input": prompt})
    return out.strip()


def main():
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = input("Prompt> ")

    # Prefer running with LangChain when available, fallback to echo
    try:
        out = run_with_langchain(user_prompt)
    except Exception:
        out = f"Agent (fallback): {user_prompt}"
    print(out)


if __name__ == "__main__":
    main()
