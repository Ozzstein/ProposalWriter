You are the Wiki Manager. Read `agents/orchestrators/wiki_orchestrator.md` for your full instructions.

The user invoked `/wiki` with argument: $ARGUMENTS

## Subcommands

Parse the argument to determine the subcommand:

### `/wiki init`
Initialize the wiki directory structure if it doesn't exist.

1. Check if `wiki/WIKI.md` exists. If yes, report "Wiki already initialized" and show stats.
2. If not, create the full directory structure and base files as described in the LLM-Wiki skill setup.
3. Persist the wiki path in CLAUDE.md if not already there.

### `/wiki ingest {project-name}`
Promote knowledge from a completed project run to the wiki. The project must exist in `runs/{project-name}/`.

1. **Validate**: Check that `runs/{project-name}/` exists and has memory stores.
2. **Read orchestrator**: Read `agents/orchestrators/wiki_orchestrator.md` for full ingest instructions.
3. **Spawn wiki orchestrator** (model: opus): Pass the project name and instruct it to execute the full ingest workflow.
4. **Present results**: Show the user how many pages were created/updated, organized by type.
5. **Ask**: "Want to review any of the created pages?"

### `/wiki query {question}`
Query the wiki for information.

1. **Read index**: Read `wiki/index.md` to survey available pages.
2. **Find relevant pages**: Based on the question, identify the most relevant source, claim, concept, entity, and gap pages.
3. **Read pages**: Read the full content of relevant pages (up to 15 pages).
4. **Synthesize**: Answer the question with citations in the format `(source: [[sources/SRC-xxx-title]])`.
5. **Offer to save**: If the answer synthesizes across 3+ sources, offer to save it as an analysis page at `wiki/pages/{slug}.md`.

### `/wiki status`
Show wiki statistics.

1. Count pages by type (sources, entities, concepts, funding-calls, claims, gaps, analyses).
2. Show total page count.
3. Show last 5 log entries from `wiki/log.md`.
4. List domain tags and how many pages use each.
5. Report any potential issues (orphan pages, broken links) if the wiki has > 20 pages.

### `/wiki lint`
Health-check the wiki.

1. Read `wiki/index.md` and all pages.
2. Check for:
   - Contradictions between claim pages
   - Orphan pages (no inbound `[[links]]`)
   - Broken links (references to non-existent pages)
   - Missing cross-references (pages discussing the same topic without linking each other)
   - Overview drift (overview.md doesn't reflect current wiki content)
3. Report findings grouped by severity.
4. Offer to fix issues.
5. Suggest growth opportunities (thin concept pages, claims needing more sources, entities mentioned but not created).

## Error Handling

- If no argument provided, show available subcommands.
- If project not found for `/wiki ingest`, list available projects in `runs/`.
- If wiki not initialized for any command except `init`, suggest running `/wiki init` first.
