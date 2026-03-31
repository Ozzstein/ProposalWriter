Run a review gate check. The user should specify which gate: `scope`, `evidence`, `draft`, or `submission`.

If no gate name is provided in the user's message, ask which gate to check.

## Steps

1. **Identify the project**: Read the most recent project in `runs/` or ask the user.

2. **Read state**: Read `runs/{project}/state.json`.

3. **Check criteria for the specified gate**:

### Gate: scope
Check these criteria:
- [ ] Call document parsed (`runs/{project}/intermediate/call_brief.json` exists)
- [ ] Evaluation criteria mapped (`runs/{project}/intermediate/evaluation_matrix.json` exists)
- [ ] Proposal outline created (`runs/{project}/intermediate/proposal_outline.md` exists)
- [ ] Research context documented (`runs/{project}/context.md` exists and has hypothesis)

### Gate: evidence
Check these criteria:
- [ ] Evidence store has >= 12 entries (count lines in `runs/{project}/memory/evidence_store.jsonl`)
- [ ] SOTA summary exists (`runs/{project}/intermediate/sota_summary.md`)
- [ ] Novelty map exists with >= 2 novelty anchors (`runs/{project}/intermediate/novelty_map.json`)
- [ ] Claim registry has entries (`runs/{project}/memory/claim_registry.jsonl` not empty)
- [ ] No more than 20% of claims have "unsupported" status

### Gate: draft
Check these criteria:
- [ ] All required sections have drafts (check `runs/{project}/drafts/` against `runs/{project}/intermediate/proposal_outline.md`)
- [ ] All drafts reference claim_ids (scan for CLM- patterns in draft files)
- [ ] No section has more than 2 unlinked [ASSUMPTION] markers
- [ ] Abstract exists and is within word limit

### Gate: submission
Check these criteria:
- [ ] Scientific review score >= 6.0 for all sections (read `runs/{project}/reviews/scientific_review.json`)
- [ ] No critical issues remaining in review reports
- [ ] Compliance review shows all requirements met
- [ ] All unsupported claims resolved or explicitly approved by user

4. **Report results**: For each criterion, report whether it's met or not with specific details (e.g., "Evidence store has 15 entries (need >= 12) — PASS").

5. **Update state.json**: Set `gates.{gate-name}.passed` to true if all criteria met, false otherwise.

6. **If gate fails**: List the specific blockers and recommend actions to address each one.

7. **If gate passes**: Congratulate the user and suggest the next pipeline stage.
