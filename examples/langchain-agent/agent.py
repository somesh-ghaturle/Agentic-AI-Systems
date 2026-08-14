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
    # ImportError only. A bare `except Exception` here reported "not installed" for every
    # failure including a version mismatch, which sent people to reinstall a package that
    # was already present and correct.
    try:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_openai import ChatOpenAI
    except ImportError as error:
        return (
            f"LangChain is not installed or is a version this example does not target: "
            f"{error}. Install the pinned requirements.txt."
        )

    if not os.environ.get("OPENAI_API_KEY"):
        return "OPENAI_API_KEY not set — set it to use the OpenAI model."

    template = ChatPromptTemplate.from_messages(
        [("system", PROMPT), ("human", "{input}")]
    )
    # LCEL: the pipe replaces LLMChain, which the 1.x line removed outright.
    chain = template | ChatOpenAI(temperature=0.2) | StrOutputParser()
    return chain.invoke({"input": prompt}).strip()


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
