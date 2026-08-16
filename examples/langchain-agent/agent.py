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
        from langchain_core.output_parsers import StrOutputParser  # noqa: PLC0415
        from langchain_core.prompts import ChatPromptTemplate  # noqa: PLC0415
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
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
    user_prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Prompt> ")

    # Prefer running with LangChain when available, fall back to echo.
    #
    # Broad on purpose, and the error is printed rather than swallowed — same reasoning as
    # the ImportError branch above. A fallback that hides an auth failure or a timeout
    # behind the word "fallback" sends people to debug the wrong thing.
    try:
        out = run_with_langchain(user_prompt)
    except Exception as error:  # noqa: BLE001
        out = f"Agent (fallback after {type(error).__name__}: {error}): {user_prompt}"
    print(out)


if __name__ == "__main__":
    main()
