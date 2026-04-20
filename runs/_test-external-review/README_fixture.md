# Smoke Test Fixture

This directory contains test fixtures for the `/external-review` command.

## Files

- `state.json` — Pipeline state (tracked in git)
- `inputs/reviews/round1/chat_test.md` — Sample external review comments (gitignored)
- `memory/claim_registry.jsonl` — Test claim registry (gitignored)
- `memory/evidence_store.jsonl` — Test evidence store (gitignored)
- `drafts/01_innovation.md` — Sample proposal draft (gitignored)

## Setup

All gitignored files are created automatically by the test suite. Only `state.json` and this README are tracked.

See `docs/superpowers/plans/2026-04-20-external-review.md` Task 12 for full setup instructions.
