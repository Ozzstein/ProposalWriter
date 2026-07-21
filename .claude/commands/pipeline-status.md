Show the current status of the proposal pipeline.

All counts and state come from `scripts/state.py` — run it rather than reading state.json or memory files by hand.

## Steps

1. **Find projects**: Run `python3 scripts/state.py projects`. If none found, tell the user to run `/start-proposal`.

2. **For each project**, run `python3 scripts/state.py show {project}` and render its output as:

   ```
   Project: {project_name}
   Agency: {funding_agency} | Mechanism: {mechanism}
   Created: {created_at}

   Pipeline Status:                Gates:
   [x] Call Parsing — complete     [x] Scope             — passed
   [~] Research     — in_progress  [ ] Evidence          — not passed
   [ ] Writing      — pending      [ ] Draft             — not passed
   [ ] Finance      — pending      [ ] Submission        — not passed
   [ ] Figures      — pending      [ ] External feedback — not passed
   [ ] Business plan— pending
   [ ] Review       — pending
   [ ] External rev.— pending
   ```
   (`[x]` complete/passed, `[~]` in_progress, `[ ]` pending. Legacy projects may lack the newer stages — show only the keys present in the output.)

3. **Quick stats** (from the same `show` output):
   - Evidence store / claim registry / decision log / task registry line counts (`stores`)
   - Draft and review files (`drafts`, `reviews`)
   - External feedback: render `feedback_rounds` as one line per round, e.g.
     ```
     External Review:
       Round 1: 12 resolved, 2 deferred, 1 rejected
       Round 2: 4 open, 3 resolved  ← active round
     ```
     If `feedback_rounds` is null, show "External review: not started".

4. **Show next recommended action**: Based on `current_stage`, suggest what to do next (e.g., "Next: run `/gate-check evidence` then `/write-proposal`").
