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
