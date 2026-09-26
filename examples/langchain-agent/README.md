LangChain Agent Example

A minimal example that demonstrates how to wire a prompt into a simple LangChain LLM chain.

Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
```

Run

```bash
python agent.py "Summarize the following: Agentic AI systems"
```

Notes

- This example falls back to a helpful message when `langchain` or `OPENAI_API_KEY` are not available so it is safe to include in the repo without secrets.
- Replace the chain with more advanced agent orchestration (tools, memory) as needed.

## Tests

[`tests/test_langchain_agent.py`](../../tests/test_langchain_agent.py) has 5 tests and runs with no
package and no key. LangChain is replaced with small fakes, and the tests cover this example's
own logic: the missing-package and missing-key messages, the `template | model | parser`
wiring, and the fallback naming the error it caught. Four mutations were each caught: removing
the key check, not stripping the answer, the fallback swallowing the error, and widening
`except ImportError` to `except Exception`. The last is the bug agent.py's comments record.

## What this is not

Not an agent. One prompt goes to one model and the text comes back: no tools, no loop, no
memory, no read/write distinction. It shows the LCEL wiring and the fallback behaviour when the
package or key is missing, and nothing about how a framework changes what an agent may do.

## Security

This example makes no security claim, which is why `SECURITY.md` lists it out of scope. The
read/write boundary this repository is organised around is demonstrated by `hermes-agent` and
`graph-agent`; nothing here enforces one, and none of this would be adequate as a production
service as written.
