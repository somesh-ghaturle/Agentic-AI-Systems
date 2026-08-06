---
name: example-skill
description: >
  TEMPLATE. Replace this. The description is the only part loaded until the skill fires,
  so it must state exactly when to use this and when not to — write it for a reader who
  is deciding, not for a reader who already chose. Include the literal words and phrases
  that should trigger it.
---

# Example skill

<!--
  A SKILL is domain knowledge loaded on demand.

  Use a skill when:  the agent repeatedly needs reference material it cannot infer —
                     an internal API's real shape, a domain's rules, a house format.
  Use a command when: you are repeating an instruction, not supplying knowledge.
  Use a subagent when: the work would flood your main context with intermediate output.

  The key economics: only the `description` above stays loaded. The body costs nothing
  until it fires. So the description must be precise, and the body can be generous.
-->

## When this applies

Name the concrete situations. Be specific enough that the wrong situation is obviously
excluded — a vague trigger is worse than no skill, because it fires at the wrong times and
pollutes context.

## The knowledge

The material that is hard to infer from the code: invariants, formats, the internal API's
actual behavior versus its documented behavior, the reason a surprising thing is the way
it is.

Concrete beats abstract. A real example of the correct output is worth more than three
paragraphs describing it.

## Worked example

```
Input:  <a realistic input>
Output: <exactly what correct output looks like>
```

## Common mistakes

The errors people and agents actually make here, and the correction for each. This section
is usually the highest-value part of a skill — grow it from `learnings.md`.

- **Mistake:** `<what goes wrong>` → **Instead:** `<the correct approach>`

## Supporting files

Keep large references as separate files next to this one and point at them, so they load
only when actually needed:

- `reference.md` — full detail
- `examples/` — worked cases
