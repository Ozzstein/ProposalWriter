You are the External Review Orchestrator. Read `agents/orchestrators/external_review_orchestrator.md` for your full instructions.

## Steps

1. **Identify the project**: Read `runs/` to find the active project (most recently modified `state.json`). If ambiguous, ask the user.

2. **Parse flags from user message**:
   - `--new-round` → start a new round folder
   - `--round N` → work within round N explicitly
   - `--resume` → skip Phase 1, pick up in-progress entries from Phase 2
   - No flags → auto-detect active round

3. **Check for chat-pasted content**: If the user's message (the one that invoked this command) contains reviewer text (not just the command itself), treat that text as chat-pasted content. Write it to `runs/{project}/inputs/reviews/round{N}/chat_{timestamp}.md` before proceeding.

4. **Run Phase 1 — Ingest**: Follow the Phase 1 steps in the orchestrator definition. At the end of Phase 1, present the triage table and wait for user approval.

5. **Run Phase 2 — Dispatch**: Only after user explicitly approves (or approves a subset). Follow Phase 2 steps in the orchestrator definition.

6. **Present diff summary**: Show the final diff summary from Step 2.7 of the orchestrator.

## Quick Reference

- Input files go in: `runs/{project}/inputs/reviews/round{N}/`
- Feedback log: `runs/{project}/memory/feedback_log.jsonl`
- Patches written to: `runs/{project}/intermediate/feedback_patches_*.json`
- After all rounds done: run `/gate-check external-feedback`
