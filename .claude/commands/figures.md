You are the Graphics Orchestrator. Read `agents/orchestrators/graphics_orchestrator.md` for your full instructions.

## Steps

1. **Identify the project**: Read `runs/` to find the active project (most recently modified `state.json`). If ambiguous, ask.

2. **Parse flags from user message**:
   - `F-xx` or `F-xx,F-yy,...` → only generate those figures
   - `--fal-only` → skip data-plots; only Fal.ai concept/schematic images
   - `--plots-only` → skip Fal.ai; only programmatic plots
   - `--embed` → after generation, re-run `combine_to_docx.py --with-figures`
   - No flags → generate every figure in `drafts/figures_register.md` whose status ≠ `final`

3. **Preflight**:
   - Read `runs/{project}/drafts/figures_register.md` and parse the essential-figure table.
   - Read `runs/{project}/figures/index.json` if present.
   - Ensure `/tmp/pw_venv/bin/python` exists with matplotlib + plotly + pandas + kaleido. Install any that are missing with `/tmp/pw_venv/bin/pip install ...`.
   - If any figure routes to Fal.ai, verify `FAL_KEY` is exported; if not, ask the user to run `export FAL_KEY=...` in a `!`-prefixed command first and stop.
   - Create `runs/{project}/figures/` and `runs/{project}/figures/scripts/` if needed.

4. **Classify + dispatch**:
   - For each requested figure, decide between `plot_renderer` (data-driven) and `concept_image_generator` (Fal.ai).
   - Spawn workers in parallel (one Agent tool call per figure, capped at 4 concurrent).
   - Model selection: `haiku` for simple plots, `sonnet` for Sankey/Gantt/heatmap, `opus` for DT-schematic and Fal.ai prompt generation.
   - Each worker returns a sidecar JSON conforming to `schemas/figure_spec.json`.

5. **Aggregate**:
   - Write `runs/{project}/figures/index.json` with every sidecar.
   - Update the `Status` column in `drafts/figures_register.md` (use the Edit tool, one row at a time).

6. **If `--embed` was passed**:
   - Run the DOCX combiner with the figures flag; report new file sizes.

7. **Report to user**:
   - Table of figures: `F-xx | status | generator | path | size`.
   - Any deferred figures + why.
   - Fal.ai calls used (for cost awareness).
   - Next-step suggestion (review candidates, pick seeds, `/gate-check submission`, etc.).

## Quick reference
- Worker specs: `agents/workers/graphics/plot_renderer.md`, `agents/workers/graphics/concept_image_generator.md`
- Orchestrator: `agents/orchestrators/graphics_orchestrator.md`
- Schema: `schemas/figure_spec.json`
- Output dir: `runs/{project}/figures/`
- Register: `runs/{project}/drafts/figures_register.md`
