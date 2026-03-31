Create a new proposal project.

Ask the user for:
1. **Project name** (short, kebab-case, e.g., "green-hydrogen-steel")
2. **Research topic** — What is the project about?
3. **Funding agency and instrument** — e.g., Horizon Europe RIA, Innovation Fund large-scale, ERC Starting Grant
4. **Key hypothesis or central idea**
5. **Any preliminary data or prior work** to reference
6. **Team members and roles** (if known)
7. **Target deadline** (if known)

After gathering this information:

1. Create the directory structure:
   ```
   runs/{project-name}/
   ├── state.json
   ├── context.md
   ├── memory/
   │   ├── evidence_store.jsonl
   │   ├── claim_registry.jsonl
   │   ├── decision_log.jsonl
   │   └── task_registry.jsonl
   ├── inputs/
   ├── intermediate/
   ├── drafts/
   ├── reviews/
   └── final/
   ```

2. Write `runs/{project-name}/context.md` with all the user's answers organized clearly.

3. Write `runs/{project-name}/state.json`:
   ```json
   {
     "project_name": "{project-name}",
     "funding_agency": "...",
     "mechanism": "...",
     "created_at": "YYYY-MM-DD",
     "stages": {
       "call_parsing": { "status": "pending" },
       "research": { "status": "pending" },
       "writing": { "status": "pending" },
       "review": { "status": "pending" }
     },
     "gates": {
       "scope": { "passed": false },
       "evidence": { "passed": false },
       "draft": { "passed": false },
       "submission": { "passed": false }
     }
   }
   ```

4. Initialize empty JSONL memory files (create them as empty files).

5. **Ask for call documents** — explain that two types of documents are helpful and ask if the user has either:

   - **Call document** (the work programme or call text): describes the scientific scope, objectives, expected outcomes, and evaluation criteria for the specific call topic. Save to `runs/{project-name}/inputs/call_document.*`

   - **Official application template** (the Part B Word/PDF template from the funder portal): defines the exact section structure, page limits, and formatting rules for this specific call. This is important because templates change between calls. Save to `runs/{project-name}/inputs/call_template.*`

   If the user cannot provide these now, note it in `state.json` and tell them they can add files to `inputs/` at any time before running `/parse-call`.

   If the user provides a URL to the funder portal or a specific call page, offer to retrieve the template using Firecrawl.

6. Tell the user their next step is `/parse-call` (if they have a call document) or `/research` (if they want to start with evidence gathering first).
