# Decision logs

Architectural decisions that are **not** recoverable from the code. Each record answers the
question a reader has when a file looks wrong: *was this considered, or was it missed?*

A decision belongs here when all three are true:

1. It was contested — there was a real alternative someone would reasonably pick.
2. It shows up in more than one file, so no single comment owns it.
3. Reversing it costs more than an edit.

Everything else stays as a comment next to the code it explains. This directory is not a
changelog and not a summary of the architecture; for that, read each tree's `ARCHITECTURE.md`,
[`infra/CHOOSING-A-TREE.md`](../../infra/CHOOSING-A-TREE.md), and
[`docs/THREAT-MODEL.md`](../THREAT-MODEL.md).

| # | Decision | Scope | Status |
|---|---|---|---|
| [0001](0001-dual-lock-aws.md) | Two locks on the AWS write boundary, and only one of them fails the plan | `infra/terraform-aws/` | Accepted |
| [0002](0002-azure-openai-vs-claude.md) | Azure calls Azure OpenAI while the other two trees call Claude | `infra/terraform-azure/` | Accepted |
| [0003](0003-gcp-firestore-over-spanner.md) | Two Firestore databases on GCP, not one Spanner instance | `infra/terraform-gcp/` | Accepted |
| [0004](0004-stdlib-only-examples.md) | An example gets a dependency only when the dependency is the subject | `examples/` | Accepted |

## Format

Numbered, four digits, never renumbered. Each file carries:

- **`Status: Accepted`** on the header line, with the decision date and the scope it governs.
  Superseded records keep their number and their file and gain a `Superseded by NNNN` line —
  they are not deleted, because the reasoning that was wrong is the part worth reading.
- **Context** — the constraint, with the file and line where it bites.
- **Decision** — what was chosen, in the present tense.
- **Consequences** — including the ones that are costs. A record with no costs listed has not
  been thought about.
- **Alternatives considered** — each with the reason it lost. "Not considered" is a valid entry
  and is more useful than silence.
- **What would reopen this** — the observable change that makes the decision wrong.

Assertions name a file. A decision log that cannot be checked against the tree decays into
folklore faster than the code it describes.
