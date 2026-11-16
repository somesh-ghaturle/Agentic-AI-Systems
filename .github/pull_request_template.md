## What this changes

<!-- One or two sentences. Link the plan task or issue if there is one. -->

## Why

<!-- The gap between what a document claims and what the tree does, or the property this teaches. -->

## Checks

- [ ] `python3 -m unittest discover -s tests` passes locally
- [ ] `ruff check .` passes
- [ ] Any count a document states still matches (`python3 .github/scripts/docs_counts.py .`)
- [ ] New or changed example: README says what it is not, and dependencies are pinned
- [ ] Touches a write boundary: I broke it on purpose and watched a test go red

<!-- Believe the write boundary can be bypassed? Do not open a PR. See SECURITY.md. -->
