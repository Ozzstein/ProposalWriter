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

1. **Scaffold the project** (creates the directory tree, empty memory stores, and a machine-valid `state.json` with all stages and gates):
   ```bash
   python3 scripts/state.py init {project-name} \
     --agency "{funding agency}" --mechanism "{instrument}" \
     --topic "{topic}" --deadline "{deadline}"
   ```
   Do not hand-create `state.json` or the directory tree — the script is the source of truth for the state shape. All later stage/gate updates also go through `scripts/state.py`.

2. **Write `runs/{project-name}/context.md`** with all the user's answers organized clearly (the script creates a stub — replace its body, keeping the hypothesis under a `## Hypothesis` heading so the scope gate can find it).

3. **Ask for call documents** — explain that two types of documents are helpful and ask if the user has either:

   - **Call document** (the work programme or call text): describes the scientific scope, objectives, expected outcomes, and evaluation criteria for the specific call topic. Save to `runs/{project-name}/inputs/call_document.*`

   - **Official application template** (the Part B Word/PDF template from the funder portal): defines the exact section structure, page limits, and formatting rules for this specific call. This is important because templates change between calls. Save to `runs/{project-name}/inputs/call_template.*`

   If the user cannot provide these now, tell them they can add files to `inputs/` at any time before running `/parse-call`.

   If the user provides a URL to the funder portal or a specific call page, offer to retrieve the template using Firecrawl.

4. **Archive input documents to wiki**: If call documents or supporting materials were provided, copy them to `wiki/raw/` for permanent cross-project archival:
   ```bash
   # Call documents (reusable across projects targeting the same call)
   cp runs/{project-name}/inputs/call-fiche* wiki/raw/CALL-{call-id}-fiche.*
   cp runs/{project-name}/inputs/application-form* wiki/raw/CALL-{call-id}-template.*

   # Supporting documents (research reports, feasibility studies, etc.)
   cp runs/{project-name}/inputs/{document} wiki/raw/{descriptive-name}.*
   ```
   Skip files that already exist in `wiki/raw/`. This ensures that call documents, GHG methodologies, templates, and any supporting materials are permanently available for future proposals without re-uploading.

5. Tell the user their next step is `/parse-call` (if they have a call document) or `/research` (if they want to start with evidence gathering first).
