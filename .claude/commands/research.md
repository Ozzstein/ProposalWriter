You are the Research & Evidence Orchestrator. Read `agents/orchestrators/research_orchestrator.md` for your full instructions.

## Steps

1. **Check prerequisites**: Read `runs/{project}/state.json`. Verify `call_parsing` is complete (or skip if user wants to go directly to research).

2. **Read context**: Read `runs/{project}/context.md` and `runs/{project}/intermediate/call_brief.json` (if available).

3. **Wiki check (Phase 0)**: If `wiki/WIKI.md` exists:
   - Read `wiki/index.md` to find relevant source, claim, gap, and concept pages for this project's domain
   - Read the relevant wiki pages (up to 15 most relevant)
   - Import relevant wiki claims into `runs/{project}/memory/claim_registry.jsonl` (prefix with `WIKI-CLM-xxx`)
   - Import relevant wiki sources into `runs/{project}/memory/evidence_store.jsonl` (prefix with `WIKI-SRC-xxx`)
   - Collect wiki gaps to pass to retrievers (so they focus on open gaps)
   - Report: "Imported X sources, Y claims, Z gaps from the wiki."
   - If wiki doesn't exist, skip this step silently.

4. **Spawn retrievers in parallel**: Use the Agent tool to launch these subagents simultaneously (multiple Agent calls in one message):

   **Literature Searcher** (model: haiku):
   - Include the full content of `agents/workers/retrievers/literature_searcher.md` in the prompt
   - Provide the research topic, key terms, and call context
   - If wiki sources/gaps were found in Phase 0, include them as context: "These sources are already known: [list]. Focus on these open gaps: [list]."
   - Instruct it to use the Semantic Scholar search tool and WebSearch
   - Write results to `runs/{project}/intermediate/literature_results.json`
   - Include: dedupe_key: literature_search_{project}

   **Patent Scanner** (model: haiku) [if relevant]:
   - Include `agents/workers/retrievers/patent_scanner.md`
   - Write results to `runs/{project}/intermediate/patent_results.json`
   - Include: dedupe_key: patent_scan_{project}

5. **Wait for retrievers, then spawn synthesizer**: After retriever agents complete, launch:

   **State of Art Synthesizer** (model: opus):
   - Include `agents/workers/synthesizers/state_of_art_synthesizer.md`
   - Provide all retriever output files as context
   - If wiki overview/concepts exist, include them: "The wiki provides this baseline SOTA context: [overview excerpt]. Build on it rather than starting from scratch."
   - Write SOTA summary to `runs/{project}/intermediate/sota_summary.md`
   - Write novelty map to `runs/{project}/intermediate/novelty_map.json`
   - Append to `runs/{project}/memory/evidence_store.jsonl` and `runs/{project}/memory/claim_registry.jsonl`
   - Include: dedupe_key: sota_synthesis_{project}

6. **Update state**: Mark `research` as `complete` in `state.json`.

7. **Present findings to user**:
   - Summarize the state of the art
   - Note how many sources came from the wiki vs. new searches
   - Highlight identified gaps
   - Show novelty anchors
   - Report number of sources and quality distribution
   - Flag any areas with thin evidence

8. **Ask user for direction**: Before proceeding, confirm:
   - Are these the right gaps to target?
   - Should we search more in any area?
   - Are the novelty claims reasonable?

9. **Suggest next step**: `/gate-check evidence` then `/write-proposal`.
