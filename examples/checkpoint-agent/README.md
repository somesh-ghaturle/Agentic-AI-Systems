# checkpoint-agent

Demonstrates state persistence and crash recovery for agentic systems.

```bash
python3 agent.py "action1"
python3 agent.py "action2"
python3 -c "from agent import CheckpointAgent; a = CheckpointAgent(); print(a.resume())"
```

No dependencies, no model, no key.

## The idea

An agent that can resume its work after a crash needs to persist its state externally.
This example implements a simple checkpointing mechanism that:

1. **Saves state after each action** - Writes completed actions to a JSON file
2. **Resumes from last checkpoint** - Loads previous state on initialization
3. **Is idempotent** - Re-running the same action doesn't duplicate it

## The implementation

`CheckpointAgent` is a minimal class that:

- Loads state from `state.json` on startup (or initializes empty state)
- Saves state after each action
- Provides a `resume()` method to get completed actions

The checkpoint file (`state.json`) is plain JSON, human-readable and diffable.

## The policy

Checkpointing follows three rules:

| Rule | Purpose | Implementation |
| --- | --- | --- |
| **Atomic writes** | Prevent corruption from crashes mid-write | Write to temp file, then rename |
| **Frequent checkpoints** | Minimize lost work | Save after every action |
| **Simple format** | Enable debugging and manual edits | Plain JSON, no binary |

## The bug running it found

The first version used `json.dump()` without `indent`, producing a single-line file that
git treated as binary and would not diff. The fix was one parameter:
`json.dumps(self.state, indent=2)`.

It is a small thing that matters when you are debugging a checkpoint from yesterday.

**Tests pin this now**: the test file verifies the state file is valid JSON and
contains the expected structure.

## What is simplified

The agent doesn't handle concurrent access — a real system would use file locking
or a database. The state is a simple list of strings; a real system would have
structured data.

Neither simplification changes the checkpointing contract: state is saved,
state is restored, actions are not lost.

## Related

- [Harness engineering](../../docs/agentic-system-architecture/HARNESS-ENGINEERING.md) — what survives between windows
- [harness-agent](../harness-agent/README.md) — the worked example of persistence
- [Building blocks §3](../../docs/agentic-system-architecture/BUILDING-BLOCKS.md#3-state) — state as a building block
