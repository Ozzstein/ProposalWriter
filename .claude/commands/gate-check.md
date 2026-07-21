Run a review gate check. The user should specify which gate: `scope`, `evidence`, `draft`, `submission`, or `external-feedback`.

If no gate name is provided in the user's message, ask which gate to check.

Gate criteria are computed deterministically by `scripts/gate_check.py` — do NOT judge criteria yourself; run the script and interpret its output. The script is the single source of truth for thresholds.

## Steps

1. **Identify the project**: Run `python3 scripts/state.py projects`. If exactly one project exists, use it; otherwise ask the user.

2. **Run the check**:
   ```bash
   python3 scripts/gate_check.py {project} {gate}
   ```
   The script prints the full result JSON, writes it to `runs/{project}/intermediate/gate_check_{gate}.json`, and updates `state.json` `gates.{gate}.passed` itself — do not edit state by hand.

3. **Interpret the exit code**:
   - `0` — gate passed
   - `1` — gate failed (blockers listed in the JSON)
   - `2` — project not found / usage error
   - `3` — not applicable (external-feedback gate with no feedback log; inform the user no external review has been ingested)

4. **Report results**: Present each criterion from the JSON as a pass/fail line with its notes (e.g., "Evidence store has >= 12 sources — PASS (15 unique sources)").

5. **If the gate fails**: List the specific blockers and recommend a concrete action for each (e.g., missing gap_analysis.json → re-run `/research` Phase 3; open FBK-IDs → `/external-review` to close them).

6. **If the gate passes**: Congratulate the user and suggest the next pipeline stage (scope → `/research`, evidence → `/write-proposal`, draft → `/review`, external-feedback → `/gate-check submission`, submission → export).
