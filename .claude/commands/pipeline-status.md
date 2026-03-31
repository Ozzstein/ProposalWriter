Show the current status of the proposal pipeline.

## Steps

1. **Find active projects**: List directories in `runs/` that contain a `state.json`. If none found, tell the user to run `/start-proposal`.

2. **For each project**, read `state.json` and report:

   ```
   Project: {project_name}
   Agency: {funding_agency} | Mechanism: {mechanism}
   Created: {created_at}

   Pipeline Status:
   [x] Call Parsing    — complete
   [~] Research        — in_progress
   [ ] Writing         — pending
   [ ] Review          — pending

   Gates:
   [x] Scope           — passed
   [ ] Evidence         — not checked
   [ ] Draft            — not checked
   [ ] Submission       — not checked
   ```

3. **Quick stats** (read the memory files):
   - Evidence store: {count} sources
   - Claim registry: {count} claims
   - Drafts: {list of files in drafts/}
   - Reviews: {list of files in reviews/}

4. **Show next recommended action**: Based on the current state, suggest what the user should do next (e.g., "Next: run `/gate-check evidence` then `/write-proposal`").

5. **Show any blockers**: If a gate was checked and failed, remind the user what needs to be fixed.
