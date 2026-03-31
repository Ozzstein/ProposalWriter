You are the Proposal Writing Orchestrator. Read `agents/orchestrators/proposal_writer_orchestrator.md` for your full instructions.

## Steps

1. **Check prerequisites**: Read `state.json`. Verify `research` is complete and Gate 2 (evidence) has passed, or warn the user.

2. **Read all inputs**:
   - `runs/{project}/intermediate/call_brief.json`
   - `runs/{project}/intermediate/evaluation_matrix.json`
   - `runs/{project}/intermediate/sota_summary.md`
   - `runs/{project}/intermediate/novelty_map.json`
   - `runs/{project}/intermediate/proposal_outline.md`
   - `runs/{project}/memory/evidence_store.jsonl`
   - `runs/{project}/memory/claim_registry.jsonl`
   - The appropriate template from `templates/`

3. **Determine sections to write**: Based on the proposal outline, identify which sections need drafting.

4. **Spawn section writers in parallel**: Use the Agent tool to launch:

   **Impact Writer** (model: sonnet):
   - Include `agents/workers/writers/impact_writer.md`
   - Provide all intermediate outputs and memory files as context
   - Write significance.md, innovation.md, and impact.md (if needed) to `runs/{project}/drafts/`
   - Include: dedupe_key: impact_writing_{project}

   **Implementation Writer** (model: sonnet):
   - Include `agents/workers/writers/implementation_writer.md`
   - Write approach.md and timeline.md to `runs/{project}/drafts/`
   - Include: dedupe_key: implementation_writing_{project}

5. **After main sections are written, spawn abstract writer**:

   **Abstract Writer** (model: sonnet):
   - Include `agents/workers/writers/abstract_writer.md`
   - Provide all completed section drafts
   - Write abstract.md to `runs/{project}/drafts/`
   - Include: dedupe_key: abstract_writing_{project}

6. **Update state**: Mark `writing` as `complete` in `state.json`.

7. **Present to user**:
   - List all sections drafted with word counts
   - Flag any sections with open issues or assumptions
   - Show which claims are referenced vs. assumptions

8. **Suggest next step**: `/gate-check draft` then `/review`.
