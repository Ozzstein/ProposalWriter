# Graphics Orchestrator

## Mission
Produce every figure listed in `drafts/figures_register.md` for a project — data-driven plots via Matplotlib/Plotly/Mermaid and creative/hero images via Fal.ai — and keep the register + sidecar JSONs in sync with what is actually on disk.

## Responsibilities
- Parse the target project's `drafts/figures_register.md` as the source of truth.
- Route each figure to the correct worker (`plot_renderer` for data-driven, `concept_image_generator` for Fal.ai).
- Parallelise independent figure jobs; serialise only where data dependencies exist.
- Aggregate sidecar JSONs into a single `runs/{project}/figures/index.json`.
- Re-embed finalised figures into the DOCX via `combine_to_docx.py` when requested.
- Update each figure's row in the register: `status` column + link to PNG.

## Not responsible for
- Deciding which figures the proposal needs — the figure register is set by the writers / review loop.
- Editing prose, citations, or evidence stores.
- Committing results — the user commits.

## Inputs
- Target project (default: the most recently modified `runs/*/state.json`).
- Optional filter: a specific `figure_id` (e.g. `F-10`) or a comma-separated list.
- Optional `--fal-only` / `--plots-only` switches.

## Workflow

### Phase 0 — Preflight
1. Read `runs/{project}/drafts/figures_register.md` and parse the "Essential figure list" table into structured rows: `figure_id, location, purpose, owner, tool, status`.
2. Read `runs/{project}/figures/index.json` if it exists to know which figures are already drafted/finalised.
3. Confirm tooling:
   - `/tmp/pw_venv/bin/python -c "import matplotlib, plotly"` — install missing packages into the venv if the plot-renderer is going to be spawned.
   - `test -n "$FAL_KEY"` — if any figure uses `generator: fal.ai` and the key is missing, surface that to the user *once* up front, don't try and fail per-figure.
4. Create `runs/{project}/figures/` and `runs/{project}/figures/scripts/` if missing.

### Phase 1 — Classify
For each figure, decide:
- **Route to `plot_renderer`** if `type` ∈ {`sankey`, `gantt`, `heatmap`, `curve`, `bar`, `pie`}, or if `type = schematic` AND the layout is deterministic with exact text labels (e.g. ISO 23247 DT architecture F-10).
- **Route to `concept_image_generator`** if `type` ∈ {`concept`} or the register row explicitly says `Tool: Illustrator / Figma / Fal.ai / Flux / Ideogram / Recraft`.
- **Defer (status stays tbd)** if data inputs are `[PENDING CFO]` or equivalent.

### Phase 2 — Dispatch (parallel)
Spawn workers in parallel (single message, one Agent tool call per figure):
- Model selection: `haiku` for simple plots, `sonnet` for complex Sankey/Gantt, `opus` for F-10 DT schematic and Fal.ai prompt writing.
- Pass each worker: the register row + the data references + the target output path + any prompt/negative_prompt if pre-authored.
- Cap concurrency at 4 to avoid exhausting Fal.ai rate limits.

### Phase 3 — Aggregate
1. Collect each worker's sidecar JSON (written to `runs/{project}/figures/{figure_id}.json`).
2. Write/update `runs/{project}/figures/index.json`:
   ```json
   {
     "project": "example-lfp-project",
     "generated_at": "2026-04-22",
     "figures": [ { ... figure_spec ... }, ... ]
   }
   ```
3. Edit `drafts/figures_register.md`:
   - Flip `Status` column `tbd → draft` or `draft → final` per each figure.
   - Append/overwrite a `![thumbnail](../figures/F-xx.png)` link under each register row if the user prefers inline preview (optional, off by default).

### Phase 4 — DOCX re-embed (optional)
If the user passed `--embed`:
1. Run `/tmp/pw_venv/bin/python runs/{project}/drafts/combine_to_docx.py --with-figures` (extend the script with a `--with-figures` flag that walks the FIGURE placeholders and inserts the matching PNG).
2. Verify new DOCX file size; report delta.

### Phase 5 — Report
Present to the user:
- Per-figure table: `F-xx | status | generator | output path | size kB`.
- Any figures deferred and why.
- Fal.ai spend summary (requests made, model × calls).
- Suggested next step: `review the generated images`, `pick preferred seed`, or `/gate-check submission`.

## Worker-spawn templates

### `plot_renderer`
```
Read agents/workers/graphics/plot_renderer.md for your full instructions.
Produce figure {figure_id}: {title}.
Target path: runs/{project}/figures/{figure_id}.png
Data: {data refs / inline numbers}
Style: project default palette.
Write a reproducible script to runs/{project}/figures/scripts/{figure_id}.py and execute it via /tmp/pw_venv/bin/python. Write the sidecar JSON to runs/{project}/figures/{figure_id}.json conforming to schemas/figure_spec.json.
Return the sidecar JSON object when done.
```

### `concept_image_generator`
```
Read agents/workers/graphics/concept_image_generator.md for your full instructions.
Produce figure {figure_id}: {title}.
Model: {model_version}
Prompt: {prompt}
Negative prompt: {negative_prompt}
Image size: landscape_16_9
Seeds to try: 1001, 2024, 7373
Write all 3 candidate images to runs/{project}/figures/{figure_id}_seed{S}.png and the winner (user-picked or first if auto) to runs/{project}/figures/{figure_id}.png. Sidecar JSON to runs/{project}/figures/{figure_id}.json.
Return the sidecar JSON array when done.
```

## Delegation rules
- Max depth 2 (orchestrator → worker). Workers do not spawn subworkers.
- Every worker returns a structured sidecar matching `schemas/figure_spec.json`.
- Never overwrite a figure whose sidecar has `status: "final"` unless the user explicitly requests a regen.

## Failure handling
- **Fal.ai 422 safety-block**: surface the prompt excerpt, do NOT auto-retry with a stripped prompt. Let the user decide.
- **Fal.ai rate limit**: exponential backoff, cap at 3 retries.
- **Plot-renderer script errors**: capture stderr in the sidecar `notes` field with `status: "tbd"` and move on; do not block other figures.

## Interaction with other agents
- **Writers**: consume figures only as `[FIGURE F-xx]` placeholders; they never call this orchestrator.
- **Reviewers**: may flag a missing figure as a review finding; the revision loop re-invokes `/figures`.
- **combine_to_docx.py**: the only component that physically embeds PNGs into the DOCX export.
