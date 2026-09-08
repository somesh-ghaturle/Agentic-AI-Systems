# stale-referent

**An approval binds the request. The effect depends on the request *and* the world it names.**

```bash
python3 referent.py
python3 -m unittest tests.test_stale_referent -v   # from the repository root
```

No dependencies, no model, no key.

---

## The failure

```
approve  refund(order="A-42")     reviewer is shown  $50.00, customer c-1
                                  ledger changes     amount_cents 5000 -> 500000
execute  refund(order="A-42")     gate: claim matches, allowed
                                  effect: refunded 500000 to c-1
```

The call that was approved and the call that ran are byte-identical. The fingerprint matches
because the fingerprint is over the arguments, and the arguments never changed. The gate is
consulted, it does its job, and a $5,000 refund goes out against a $50 approval.

Nothing here is a bypass. Every control does exactly what it says it does.

## Why the fingerprint cannot catch it

`infra/*/src/shared/contracts.py` hashes the action and the arguments a human approved, and the
executor re-checks that hash before running. That check is worth having, and it is the wrong
shape for this failure:

```python
fingerprint("refund", {"order": "A-42"})   # before the ledger moves
fingerprint("refund", {"order": "A-42"})   # after — identical
```

**A hash over a reference certifies the reference, not the thing referred to.** Arguments are
usually references: an order ID, a user ID, a resource ARN, a feature flag name. What the
reviewer decides about is the *resolved* value, which nobody records because the gate was
designed to bind calls.

## What separates the two

`drift()` asks a different question. Not *"is this the call that was approved?"* but *"do the
facts that decision was made about still hold?"*

```python
approval = gate.review("refund", {"order": "A-42"})   # shown: {'amount_cents': 5000, ...}
LEDGER["A-42"]["amount_cents"] = 500_000
drift(approval)          # {'amount_cents': (5000, 500000)}
execute_bound(gate, approval)
# Refused: binding: approved facts no longer hold (amount_cents: 5000 -> 500000)
```

The refusal names the field and both values, because *"approval no longer valid"* sends an
operator to re-approve the same thing rather than to ask what changed underneath it.

## The claim is asserted, not described

`TestTheGateIsNotEnough` runs the entire gate suite programmatically *after* the wrong amount
has gone out, and asserts it still passes. A green gate suite is not evidence that what was
approved is what happened.

Five mutations, all caught: dropping the `claim is None` branch, narrowing `drift()` to the
amount alone, `execute_bound` skipping the drift check, `review()` not recording what was shown,
and `execute_bound` skipping the gate once it has checked drift.

## How this differs from its siblings

| Example | The gate is… | What goes wrong |
|---|---|---|
| [second-path](../second-path/README.md) | correct, and off the path | a second route reaches the effect without it |
| [tool-discovery](../tool-discovery/README.md) | correct, and the wrong shape | a filter where a structure was needed |
| **stale-referent** | correct, and on the path | the call is the approved one; the world is not |

In a system that has fixed the first two, this one is what is left — and it gets more likely,
not less, as the agent gains write access to the same stores its approvals refer to.

## What this does not teach

Not a locking or transaction design. Re-checking at execution time closes the window the
example demonstrates; it does not close the window between the check and the effect. That is
the same problem one layer down, and the honest answers there are a conditional write, an
optimistic-concurrency token, or executing against the snapshot the reviewer saw rather than
against the store.

Not an argument that approvals should carry every fact. `shown` is what the reviewer was
actually given. Recording more than that is theatre; recording less is this example.

---

- [ENVIRONMENT-ENGINEERING.md §2](../../docs/agentic-system-architecture/ENVIRONMENT-ENGINEERING.md) — the chapter this belongs to
- [second-path](../second-path/README.md) — the other way a correct gate stops mattering
