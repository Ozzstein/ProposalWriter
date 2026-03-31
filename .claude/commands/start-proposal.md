Create a new proposal project.

Ask the user for:
1. **Project name** (short, kebab-case, e.g., "crispr-sickle-cell")
2. **Research topic** — What is the research about?
3. **Funding agency and mechanism** — e.g., NIH R01, NSF, EU Horizon
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

5. Ask the user if they have a funding call document to upload to `runs/{project-name}/inputs/`.

6. Tell the user their next step is `/parse-call` (if they have a call document) or `/research` (if they want to start with evidence gathering).
