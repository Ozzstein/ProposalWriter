# ProposalWriter — Mission Control UI

A local web dashboard for monitoring and driving the ProposalWriter multi-agent
pipeline. Reads project state from `runs/{project}/`, renders the agent graph
from `agents/`, and streams live activity from `runs/_events.jsonl` (written by
the `emit_event.py` hook).

## Architecture

```
ui/
  shared/   Shared TypeScript types (events, state, memory, agent graph)
  server/   Hono backend on 127.0.0.1:7777 — project/memory/agent-graph endpoints
  web/      React + Vite + Tailwind + shadcn-style primitives — dashboard UI
```

Telemetry is file-based: every tool call in Claude Code fires the
`emit_event.py` hook, which appends one JSON line to `runs/_events.jsonl`. The
UI tails that file over SSE (Phase 2).

## Prerequisites

- Node.js ≥ 20
- Python ≥ 3.10 (already required by the pipeline itself)

## First run

```sh
cd ui
npm install
npm run dev
```

This starts both services in parallel:

| Service | URL                       | Source          |
| ------- | ------------------------- | --------------- |
| API     | http://127.0.0.1:7777/api | `ui/server/`    |
| Web     | http://127.0.0.1:5173     | `ui/web/`       |

Open the web URL in your browser. The dev server proxies `/api/*` to the
backend, so you only need one browser tab.

## What's in which phase

- **Phase 1:** Overview, System Graph, Memory (with non-destructive flag/note
  overrides), project switcher. `emit_event.py` is already running, so event
  history accumulates from day one.
- **Phase 2:** SSE activity feed, streaming event rows, filter by hook/tool,
  pause/resume, and live node-pulsing on the System Graph.
- **Phase 3:** SDK-driven stage launch / resume via the Pipeline page, session
  tracking and stop control on the Sessions page.

## Running a stage from the UI

The Pipeline page lists every slash command as a card. Clicking **Run** opens a
confirm drawer; clicking **Resume** reuses the last SDK session id recorded for
that stage on this project. Live progress streams into the Activity page, and
matching nodes on the System Graph pulse as tool uses appear in the feed.

Stage launches use `@anthropic-ai/claude-agent-sdk` with the slash command's
markdown body as the prompt, `cwd = runs/<project>/`, and `resume = <sdk-session>`
when resuming. Session metadata lives in `ui/server/data/sessions.jsonl`.

## Environment variables

| Var           | Default         | Meaning                            |
| ------------- | --------------- | ---------------------------------- |
| `PW_UI_PORT`  | `7777`          | Backend port                       |
| `PW_UI_HOST`  | `127.0.0.1`     | Backend bind host (local-only)     |

## Notes

- The UI never rewrites JSONL memory stores. Flag/reject/note actions append
  to `runs/{project}/memory/overrides.jsonl` instead, so the pipeline's
  append-only invariant stays intact.
- If you run Claude Code in multiple windows against the same repo, both
  sessions emit into the same `runs/_events.jsonl`. Each event carries
  `session_id` for filtering.
- `runs/_events.jsonl` and `runs/_events.errors.log` are gitignored.
