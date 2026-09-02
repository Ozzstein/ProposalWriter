# Proposal Agency — web UI

React + Vite dashboard for the agency server (`agency serve`, FastAPI on
`127.0.0.1:7777`). Pages: Overview (stages, gates, graph counts, spend),
Pipeline (run any stage, flags, gate checks), Inbox (questions, approvals,
forms and chat turns that runs block on), Runs (job DAG per run with cost),
Activity (live event stream), Agents (catalogue graph with live pulses),
Graph (browse sources, claims, gaps, anchors, sections, findings, decisions).

```sh
cd ui && npm install
npm run dev          # http://127.0.0.1:5173, proxies /api to :7777
npm run build        # writes web/dist; `agency serve` then serves it at /
npm run typecheck
```

`ui/shared` holds the TypeScript types mirrored from the Python models.
