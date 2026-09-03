# Proposal Agency — developer notes

This repository is a standalone application built on the Claude Agent SDK
(`agency/` Python package + `ui/web` React app). It is **not** a Claude Code
project any more: there are no slash commands, subagent stubs or hook scripts
to run from an interactive session. Use this file as orientation when working
on the code.

- Architecture and design decisions: `docs/architecture.md`
- Agent prompts and contracts: `agents/<name>/{contract.yaml,prompt.md}`,
  conventions prepended to every system prompt: `agents/conventions.md`
- Funder packs (outline templates, rubric hints, hard rules): `packs/`
- Gate thresholds live only in `agency/policy/thresholds.py`
- Tests: `.venv/bin/python -m pytest -q` (mocked SDK); `tests/test_sdk_smoke.py`
  runs real model calls when `ANTHROPIC_API_KEY` is set
- UI: `cd ui && npm run typecheck && npm run build`

When changing an agent contract, run `agency doctor` — the catalogue is
validated at startup and the doctor reports missing prompts, unknown output
models or connectors.
