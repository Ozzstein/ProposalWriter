# Proposal Agency

An agentic grant-proposal writing system built on the
[Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk). It takes a
research idea and a funding call through ideation, evidence gathering,
drafting, a simulated evaluator panel, external reviewer feedback and export —
with every claim traced to sources in a provenance graph and every human
decision captured in an inbox.

```
idea ──▶ parse-call ──▶ ideate ──▶ research ──▶ write-proposal ──▶ review ──▶ external-feedback ──▶ export
                                     │              │  ▲               │(loop: revise → re-score)
                                     │        finance / figures / business-plan (optional)
                                     └─ knowledge base: promoted after a project, imported by the next
```

Ideation can also run before the call (exploratory mode); parse-call then aligns the hypothesis with the call and asks you to configure the scope: finance, business plan, figures and external review as excluded / included / required.

## What makes it different

- **The proposal is a graph, not a folder.** Sources, claims, gaps, novelty
  anchors, sections, figures, review findings, panel scores, feedback and
  decisions are typed nodes in SQLite with provenance edges
  (`supported_by`, `cites`, `addresses`, `resolved_by`, `promoted_to`, …).
  Gates, reviews and exports are queries over that graph.
- **The call drives the pipeline.** `parse-call` turns the call document into a
  `CallSpec` (sections, weighted criteria, eligibility and hard rules, limits).
  A funder pack (`packs/`) adds outline templates, rubric hints and known hard
  rules. The planner generates one drafting job per required section.
- **Agents are contracts.** Each agent in `agents/<name>/` has a
  `contract.yaml` (role, model tier, tools, connectors, output model, budget,
  acceptance checks) and a `prompt.md`. The engine composes them; agents never
  orchestrate, never spawn subagents and never write to the graph except through
  validated tools.
- **Control flow is code; judgment is the model.** Stage order, gates, budgets,
  retries, ID allocation and store writes are deterministic Python. Model calls
  are bounded, structured (`output_format` with the pydantic schema) and
  idempotent.
- **One human channel.** Questions, approvals, forms and interview turns go
  through a persisted inbox. Runs block on it and survive server restarts.
- **Quality is a loop.** `review` runs scientific and compliance reviews plus a
  simulated evaluator panel, ranks revisions by expected score gain, redrafts
  the weakest sections and re-scores until the predicted score plateaus.

## Quick start

```bash
git clone https://github.com/Ozzstein/ProposalWriter.git && cd ProposalWriter
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"   # or: python -m venv .venv && .venv/bin/pip install -e ".[dev]"
cp secrets.example.json secrets.json                                    # add ANTHROPIC_API_KEY (or export it)
.venv/bin/agency doctor

.venv/bin/agency init "Green hydrogen DRI steel" --funder "Horizon Europe" --mechanism RIA \
    --hypothesis "H2-based DRI with heat integration cuts steelmaking emissions by 90%"
# drop the call document into workspace/projects/green-hydrogen-dri-steel/inputs/, then:
.venv/bin/agency run green-hydrogen-dri-steel parse-call     # questions are asked on stdin
.venv/bin/agency run green-hydrogen-dri-steel research
.venv/bin/agency status green-hydrogen-dri-steel
```

Or use the web UI:

```bash
cd ui && npm install && npm run build && cd ..
.venv/bin/agency serve            # http://127.0.0.1:7777 — projects, pipeline, inbox, runs, graph, agents
```

## How to use it

The app always tells you the next step. On the Overview page a **Next step** card names the action,
explains why, and carries the button that does it; `agency next PROJECT` prints the same guidance
in the terminal. The path is:

1. **Create a project** (name, funder, your central idea). No idea yet? Leave the hypothesis empty
   and the first step becomes the ideation interview.
2. **Upload the call document and parse it.** The parsed call defines sections, criteria,
   requirements and gates; you approve it in the Inbox.
3. **Confirm eligibility.** Disqualifying requirements the parser found are listed on the Overview;
   mark each met / not applicable (`agency requirement PROJECT E1 met`). The scope gate opens.
4. **Research → Draft → Review → Export.** Run each from the Next step card or the Pipeline page.
   Finance, figures, business plan and external feedback are optional side steps the guidance
   proposes only when the call needs them.
5. **Answer the Inbox** whenever its badge lights up: runs block on your questions, approvals and
   forms and resume when you answer.

Prefer to delegate? Type a goal into the **Planner** on the Pipeline page; the planning agent
proposes a campaign of stage runs, you approve it once, and the engine executes it.

## Stages

| Stage | What happens | Gate |
|---|---|---|
| `parse-call` | `CallSpec` from the call document (+ eligibility parser, funder pack), outline, your approval, scope configuration, concept alignment | → `scope` |
| `ideate` | Interview (through the inbox) → 2–3 candidate framings → shallow prior-art probes → evaluator scoring → you choose; the hypothesis is written into the project context | — |
| `research` | Knowledge-base import, parallel retrieval (literature, EU repositories, patents) with reserved ID ranges, SOTA synthesis with claim registration, novelty map, gap analysis | `scope` → `evidence` |
| `write-proposal` | One writer job per required section: excellence first, impact + implementation in parallel, abstract last; drafts ingested as `Section` nodes with `cites` edges | `evidence` → `draft` |
| `finance` | Inputs from workbooks or an inbox form (schema-validated), financial model with hard-threshold checks, narrative sections, financial red-team with escalation | — |
| `figures` | Figure register → classify → render in parallel (Matplotlib/Plotly or Fal.ai) → index | — |
| `business-plan` | Batched discovery interview (persisted per batch), fact synthesis, four writers, red-team, assembly | — |
| `review` | Scientific + compliance reviews, simulated panel, ranked revision plan, revise → re-score loop | `draft` → `submission` |
| `external-feedback` | Reviewer files or pasted text → parsed comments → inbox triage → specialist routing → verbatim patches → round summary | → `external_feedback` |
| `export` | Markdown + DOCX with a reference list built from cited sources | `submission` |
| `plan` | The planning agent reads the project state (stages, gates, blockers, runs, cost) and your goal, proposes a campaign of stage runs with flags, you approve it in the inbox, the engine executes it and re-plans once if a step stops | — |

Gates block by default; `--force` records a `gate_override` decision. All
thresholds live in `agency/policy/thresholds.py` and can be overridden per pack
or in `agency.toml`.

## CLI

```
agency init NAME [--funder --mechanism --topic --deadline --hypothesis --id]
agency projects | status PROJECT | gate PROJECT GATE [--no-write]
agency next PROJECT                      # what to do now, and the command that does it
agency requirement PROJECT REQ_ID met|unmet|not_applicable
agency run PROJECT STAGE [-f key=value ...] [--resume] [--force]
agency plan PROJECT --goal "..." [--budget USD] [--max-replans N] [--no-execute]
agency inbox [PROJECT] | agency inbox --item ID --answer TEXT
agency kb status | promote PROJECT | query "question" | lint [--fix] | export [DIR]
agency import-legacy [PROJECT] [--runs-dir DIR]      # old runs/{project}/ layouts
agency export-graph PROJECT                            # nodes.jsonl + edges.jsonl
agency serve [--port]  |  agency doctor
```

## Layout

```
agency/            the application (see docs/architecture.md)
  domain/          pydantic models: graph nodes/edges, CallSpec, runs, jobs, inbox
  store/           Store interface + SQLAlchemy implementation (SQLite today), blob store
  graph/           typed repo over the store (provenance, claim/source lookups)
  policy/          gate rules + the single thresholds table
  catalogue/       agent contracts + prompt composition
  sdk/             ClaudeAgentOptions from a contract; one-shot agents and interactive sessions
  tools/, hooks/   in-process MCP tools (graph read/write, inbox) and guard/telemetry hooks
  connectors/      external MCP servers (academic-search, firecrawl)
  engine/          stage plans (job DAGs), scheduler, runtime, graph<->files materialisation
  jobs/            the ten stages
  inbox/           the human channel (web + terminal adapters)
  kb/              cross-project knowledge base
  server/          FastAPI API + SSE, serves ui/web/dist
agents/            <name>/contract.yaml + prompt.md, conventions.md
packs/             funder packs (innovation-fund, horizon-europe-ria, nih-r01, nsf, generic)
schemas/           JSON schemas (kept for validation of legacy-shaped inputs such as financial_inputs)
mcp-servers/       academic-search FastMCP server (PubMed, arXiv, Scopus, Crossref, Europe PMC, Unpaywall)
ui/                React dashboard
workspace/         (gitignored) SQLite db, blobs, per-project working dirs, kb vault
```

## Configuration

`agency.toml` (workspace root, model ids per tier, budgets, concurrency, gate
thresholds, server port) and `secrets.json` (API keys, exported only to the
agent processes whose contracts declare them). Environment overrides:
`AGENCY_HOME`, `AGENCY_DB_URL`, `AGENCY_MODEL_{FAST,BALANCED,REASONING}`,
`AGENCY_PORT`, `ANTHROPIC_API_KEY`.

## Tests

```bash
.venv/bin/python -m pytest -q          # mocked SDK: store, gates, catalogue, engine, all stages, server, kb
ANTHROPIC_API_KEY=... .venv/bin/python -m pytest -q tests/test_sdk_smoke.py   # real model calls, a few cents
```

## License

All rights reserved.
