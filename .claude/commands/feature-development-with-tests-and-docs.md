---
name: feature-development-with-tests-and-docs
description: Workflow command scaffold for feature-development-with-tests-and-docs in openshorts.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /feature-development-with-tests-and-docs

Use this workflow when working on **feature-development-with-tests-and-docs** in `openshorts`.

## Goal

Implements a new feature, adds configuration UI, tests, and documentation for it.

## Common Files

- `custom_ai_client.py`
- `sitecustomize.py`
- `dashboard/src/components/KeyInput.jsx`
- `tests/test_custom_ai_client.py`
- `CUSTOM_AI_ENDPOINT.md`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Implement core logic in backend (e.g., custom_ai_client.py, sitecustomize.py)
- Add or update frontend configuration components (e.g., dashboard/src/components/KeyInput.jsx)
- Write or update tests for new feature (e.g., tests/test_custom_ai_client.py)
- Document the feature and its setup (e.g., CUSTOM_AI_ENDPOINT.md)

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.