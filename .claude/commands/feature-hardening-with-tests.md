---
name: feature-hardening-with-tests
description: Workflow command scaffold for feature-hardening-with-tests in openshorts.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /feature-hardening-with-tests

Use this workflow when working on **feature-hardening-with-tests** in `openshorts`.

## Goal

Improves or fixes an existing feature and updates corresponding tests.

## Common Files

- `custom_ai_client.py`
- `sitecustomize.py`
- `tests/test_custom_ai_client.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Apply fixes or improvements in backend files (e.g., custom_ai_client.py, sitecustomize.py)
- Update or add tests to cover new or changed behavior (e.g., tests/test_custom_ai_client.py)

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.