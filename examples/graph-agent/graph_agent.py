"""The same read/write split as hermes-agent, expressed as an explicit graph.

    python3 graph_agent.py

The point of comparison is deliberate. hermes-agent enforces its write boundary in ordinary
application code; this routes the identical request through a LangGraph state graph. Reading
them side by side is the clearest way to see what the graph actually buys — and what it costs.

What it buys, concretely, is the approval gate. In hermes-agent the pause for human approval is
a proposal object the caller has to hold and hand back. Here it is `interrupt()`: the graph
suspends, its state goes to a checkpointer, and resumption is `Command(resume=...)` against the
thread id. An approval that takes a day is the same code as one that takes a second.

No model and no key. The node functions are deterministic, which keeps the example about the
graph rather than about a prompt.
"""

import sys

# TypedDict comes from typing, not typing_extensions. A try/except further down used to
# fall back to typing_extensions "for Python 3.9 and below", which was dead in two
# independent ways: typing.TypedDict has existed since 3.8, so the branch was unreachable,
# and this example requires 3.10+ regardless because langgraph will not install below it.
# Its only real effect was an undeclared dependency — the fallback named a package
# requirements.txt did not pin, which worked solely because langgraph pulls it in
# transitively. .github/scripts/example_deps.py now fails on exactly that.
from typing import Any, Optional, TypedDict

# The langgraph import is soft, and that is not politeness — it is what makes this file
# testable. The first version called sys.exit() here, so importing the module without
# langgraph installed killed the interpreter. A test runner cannot import a module that exits
# the process, which is why this example had no tests at all while harness-agent had 36, and
# why the fail-open classifier bug below had nothing stopping it from coming back.
#
# The routing logic needs no framework. Only build() and approval() do, so only they raise.
try:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.graph import END, START, StateGraph
    from langgraph.types import Command, interrupt

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised by running without the dependency
    LANGGRAPH_AVAILABLE = False

MISSING = (
    "langgraph is not installed.\n"
    "    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt\n"
    "Requires Python 3.10+."
)


class State(TypedDict, total=False):
    """The shared state object every node reads and writes.

    A graph's state being one declared type is half of what makes the topology reviewable: you
    can see what flows between nodes without tracing calls. The other half is the edges.
    """

    request: str
    kind: str
    findings: list[str]
    proposal: Optional[dict[str, Any]]
    approved: bool
    answer: str


# --- the read side -------------------------------------------------------------------

KNOWLEDGE = {
    "refund policy": "Refunds are available within 30 days of delivery.",
    "shipping": "Standard shipping is 3-5 business days.",
    "order 4471": "Order 4471 shipped on 2026-08-02, delivered 2026-08-05.",
}

# Action phrases, not bare nouns. The first version of this list held "refund", and
# "what is the refund policy" — a question — routed to the write branch and produced a refund
# proposal for an order the user never mentioned.
#
# That is worth leaving documented rather than quietly fixing, because it is the characteristic
# failure of a read/write split: the classifier fails *open*, toward the privileged path. A
# keyword list is the wrong shape for this job — a noun that appears in both a question and a
# command cannot separate them.
#
# hermes-agent avoids the problem entirely by never inferring intent from text: the caller names
# the tool, and the tool is registered as read or write. That is the more robust design, and the
# reason this example keeps a classifier at all is that the graph needs a conditional edge to
# demonstrate. Where you can dispatch on a declared tool instead of guessing from a string, do.
WRITE_PHRASES = (
    "issue a refund",
    "issue refund",
    "cancel order",
    "cancel the order",
    "delete",
    "charge",
)

QUESTION_OPENERS = ("what", "how", "when", "where", "why", "who", "is ", "does ", "can ")


def classify(state: State) -> State:
    """Read or write? The only branch in the graph that decides anything.

    Questions are reads regardless of the nouns in them, checked first. Then explicit action
    phrases. Anything unmatched falls to read, which is the safe default here — an
    unrecognised request that reaches the read branch returns "No matching knowledge", while
    one that reaches the write branch drafts a proposal.
    """
    request = state["request"].lower().strip()
    if request.startswith(QUESTION_OPENERS) or request.endswith("?"):
        return {"kind": "read"}
    kind = "write" if any(phrase in request for phrase in WRITE_PHRASES) else "read"
    return {"kind": kind}


def retrieve(state: State) -> State:
    request = state["request"].lower()
    findings = [text for key, text in KNOWLEDGE.items() if key in request]
    return {"findings": findings or ["No matching knowledge."]}


# --- the write side ------------------------------------------------------------------


def draft(state: State) -> State:
    """Produce a *proposal*, never an effect.

    Same rule as hermes-agent: the part of the system that reasons does not get a handle on
    the part that acts. Here that separation is visible as two nodes with an interrupt
    between them.
    """
    return {
        "proposal": {
            "action": "issue_refund",
            "order": "4471",
            "amount": "49.99",
            "reason": state["request"],
        }
    }


def approval(state: State) -> State:
    """Suspend the graph until a human answers.

    `interrupt` is the thing a plain loop has to improvise. The graph stops here, its state is
    checkpointed, and the process may exit. Resuming is a `Command(resume=...)` against the
    same thread id — hours or days later, from a different process.
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(MISSING)
    decision = interrupt(
        {
            "question": "Approve this action?",
            "proposal": state["proposal"],
        }
    )
    return {"approved": bool(decision)}


def execute(state: State) -> State:
    if not state.get("approved"):
        return {"answer": "Refused: the action was not approved."}
    proposal = state["proposal"]
    return {
        "answer": f"Executed {proposal['action']} for order {proposal['order']} "
        f"({proposal['amount']})."
    }


def respond(state: State) -> State:
    if state.get("answer"):
        return {}
    return {"answer": " ".join(state.get("findings", []))}


# --- the topology --------------------------------------------------------------------


def route(state: State) -> str:
    """The conditional edge. Declared here, not discovered in a log."""
    return "draft" if state["kind"] == "write" else "retrieve"


def build(checkpointer=None):
    """Assemble and compile the graph.

    Written as a function returning a compiled graph so the topology is a value that tests can
    inspect — `graph.get_graph().draw_mermaid()` renders the diagram in architecture.md, which
    is what "the topology is reviewable" means in practice.

    `checkpointer` is the production seam. It used to be hardcoded to `InMemorySaver()`, with
    the README telling you to edit this line for a real deployment — which meant the one thing
    standing between the demo and a durable approval gate was a source edit nobody could test.
    Passing it in makes durability a deployment choice instead:

        # pip install langgraph-checkpoint-sqlite
        from langgraph.checkpoint.sqlite import SqliteSaver
        with SqliteSaver.from_conn_string("approvals.db") as saver:
            graph = build(checkpointer=saver)

    The default stays in-memory because the demo and the test suite should need no database,
    and because a durable checkpointer that silently defaults on would put approval state on
    disk without anyone asking for it.

    What the injected checkpointer actually buys is visible in the tests: a *second* graph
    built over the same checkpointer resumes a thread the first one suspended. The state lives
    in the checkpointer, not in the graph object — which is the property a process restart
    depends on, and the one an in-memory default cannot survive.
    """
    if not LANGGRAPH_AVAILABLE:
        raise ImportError(MISSING)

    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("retrieve", retrieve)
    builder.add_node("draft", draft)
    builder.add_node("approval", approval)
    builder.add_node("execute", execute)
    builder.add_node("respond", respond)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify", route, {"retrieve": "retrieve", "draft": "draft"}
    )
    builder.add_edge("retrieve", "respond")
    builder.add_edge("draft", "approval")
    builder.add_edge("approval", "execute")
    builder.add_edge("execute", "respond")
    builder.add_edge("respond", END)

    # The checkpointer is what makes interrupt() durable rather than a pause. The default is
    # in-memory and dies with the process; see the docstring for the swap and why it is an
    # argument rather than an edit.
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def run(graph, request, thread_id, approve=None):
    """Run one request, answering the interrupt if the graph raises one."""
    config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke({"request": request}, config)

    if "__interrupt__" in result:
        if approve is None:
            # Reached when a request routes to the write branch unexpectedly. Raising beats
            # resuming with None, which LangGraph rejects further down with a much less
            # obvious error — this is the message that names the actual problem.
            raise RuntimeError(
                f"{request!r} suspended for approval but no decision was supplied; "
                "it was classified as a write"
            )
        payload = result["__interrupt__"][0].value
        print(f"    graph suspended: {payload['question']}")
        print(f"    proposal: {payload['proposal']}")
        print(f"    human answers: {approve}")
        result = graph.invoke(Command(resume=approve), config)

    return result["answer"]


def main():
    if not LANGGRAPH_AVAILABLE:
        sys.exit(MISSING)
    graph = build()

    print("Read request")
    print("-" * 12)
    print(f"  {run(graph, 'what is the refund policy', 'thread-read')}\n")

    print("Write request, approved")
    print("-" * 23)
    print(f"  {run(graph, 'issue a refund for order 4471', 'thread-yes', approve=True)}\n")

    print("Write request, refused")
    print("-" * 22)
    print(f"  {run(graph, 'issue a refund for order 4471', 'thread-no', approve=False)}\n")

    print("The topology, as the graph itself reports it")
    print("-" * 44)
    print(graph.get_graph().draw_mermaid())


if __name__ == "__main__":
    main()
