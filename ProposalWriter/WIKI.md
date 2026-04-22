# Wiki Schema

## Purpose
Persistent, cross-project knowledge base for grant proposal writing. Captures evidence, claims, gaps, competitor intelligence, and funding call analysis so that new proposals build on prior research instead of starting from scratch.

## Conventions

### Filenames
- Lowercase, hyphenated (e.g. `lfp-calcination.md`)
- Source pages: `SRC-xxx-short-title.md` (matches evidence_store source_id)
- Claim pages: `CLM-xxx-short-description.md` (matches claim_registry claim_id)
- Gap pages: `GAP-xxx-short-description.md` (matches gap_analysis gap_id)
- Entity pages: `entity-name.md` (e.g. `freyr-battery.md`)
- Concept pages: `concept-name.md` (e.g. `lfp-cathode-active-material.md`)
- Funding call pages: `call-id.md` (e.g. `innovfund-2025-nzt.md`)

### Cross-links
- Use Obsidian wiki-link format: `[[page-name]]` or `[[page-name|display text]]`
- Never use plain markdown links `[text](path)` for internal pages
- Every claim page MUST link to its supporting source pages
- Every gap page MUST link to the evidence that documents it
- Every source page MUST link to related entity and concept pages

### Citations
- Within wiki pages: `(source: [[sources/SRC-xxx-short-title]])`
- When imported into a project's claim_registry: prefix with `WIKI-` (e.g. `WIKI-CLM-005`)

### Domain tags
Tags define knowledge domains. Use consistently across pages:
- `lfp-cathode-materials`, `nmc-cathode-materials`, `solid-state-battery`
- `digital-twins-manufacturing`, `process-analytical-technology`, `iso-23247`
- `electrification-process-heat`, `ghg-emission-avoidance`, `decarbonization`
- `eu-innovation-fund`, `eu-horizon-europe`, `nsf`, `nih`
- `spray-drying`, `calcination`, `coprecipitation`
- `battery-supply-chain`, `strategic-autonomy`, `critical-raw-materials`

Add new tags as needed, but check existing tags first to avoid duplicates.

## Frontmatter template

```yaml
---
title: Page Title
type: source | entity | concept | funding-call | claim | gap | analysis | overview
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: N
tags: []
---
```

### Extended frontmatter by page type

**Sources** (`pages/sources/`):
```yaml
---
title: Paper Title
type: source
source_id: SRC-xxx
created: YYYY-MM-DD
updated: YYYY-MM-DD
authors: "Author et al."
year: YYYY
source_type: paper | patent | report | policy_document | standard | technical_report
quality: high | medium | low
doi: "optional"
url: "optional"
origin_project: project-name  # which run first found this source
tags: []
---
```

**Claims** (`pages/claims/`):
```yaml
---
title: Claim short description
type: claim
claim_id: CLM-xxx
created: YYYY-MM-DD
updated: YYYY-MM-DD
status: supported | assumption | disputed
confidence: 0.0-1.0
category: strategic | technical | novelty | sota | research_gap
supported_by: [SRC-xxx, SRC-yyy]  # source_ids
origin_project: project-name
tags: []
---
```

**Gaps** (`pages/gaps/`):
```yaml
---
title: Gap short description
type: gap
gap_id: GAP-xxx
created: YYYY-MM-DD
updated: YYYY-MM-DD
severity: critical | high | medium | low
strategic_importance: 1-10
gap_type: research | technology | application | integration | regulatory
addressed_by_projects: []  # which runs target this gap
tags: []
---
```

**Entities** (`pages/entities/`):
```yaml
---
title: Entity Name
type: entity
entity_type: organization | project | platform | consortium
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: N
tags: []
---
```

**Concepts** (`pages/concepts/`):
```yaml
---
title: Concept Name
type: concept
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_count: N
tags: []
---
```

**Funding Calls** (`pages/funding-calls/`):
```yaml
---
title: Call Name
type: funding-call
call_id: "CALL-ID-STRING"
agency: "Innovation Fund (CINEA)" | "Horizon Europe" | "NSF" | "NIH"
deadline: YYYY-MM-DD
created: YYYY-MM-DD
updated: YYYY-MM-DD
projects_targeting: []  # which runs target this call
tags: []
---
```

## Page types

- **sources/** — One page per ingested evidence source: bibliographic data, summary, key claims, links to entities/concepts. Maps 1:1 to evidence_store.jsonl entries.
- **entities/** — Organizations, research projects, platforms, consortia. Updated each time a new source mentions them. Tracks competitor status and latest intelligence.
- **concepts/** — Technical themes, methods, frameworks, terminology. Synthesize across sources, note contradictions, track evolution of understanding.
- **funding-calls/** — Parsed call documents: eligibility criteria, scoring rubrics, section structures, deadlines. Reusable across proposals targeting the same call.
- **claims/** — Pre-validated technical claims backed by evidence. Each claim links to supporting sources and has a confidence score. Maps to claim_registry.jsonl entries.
- **gaps/** — Documented research, technology, or application gaps. Each gap links to evidence and tracks which projects address it. Maps to gap_analysis.json entries.
- **root pages** — Analyses, comparisons, query answers worth preserving.
- **overview.md** — High-level domain synthesis, updated after significant ingests.

## Raw content archive

`wiki/raw/` is the **permanent archive for ALL information** flowing through the system. Every document, article, patent, call fiche, supporting material, and downloaded content lives here. The evidence_store keeps only a short extract; `wiki/raw/` preserves the full original.

### What goes into raw/ (everything)
- **Publications**: Full-text articles from ScienceDirect, Unpaywall, arXiv, PubMed, Europe PMC, Firecrawl scrapes. Even abstracts-only when full text is paywalled.
- **Patents**: Full patent pages scraped from Google Patents, Espacenet
- **Call documents**: Call fiches, application templates, GHG methodology guides, official guidance PDFs
- **Supporting documents**: Research reports, feasibility studies, technical notes, vendor datasheets
- **Policy documents**: EU regulations, NECP plans, strategy papers
- **Fun facts & misc**: Anything worth keeping — press releases, competitor announcements, conference slides, internal memos
- **Images/diagrams**: Save to `wiki/raw/assets/` (Obsidian attachment folder)

### How content gets into raw/
- **Automatically by retriever agents**: literature_searcher, web_scraper, and patent_scanner archive every downloaded file after retrieval
- **Automatically by call_parser**: Call documents are archived during `/parse-call`
- **Automatically by start-proposal**: Input documents are archived when a project is initialized
- **Manually**: Drop PDFs, clipped articles, or any files you want to preserve

### Naming convention
- Articles: `{source_id}-{short-slug}.md` (e.g. `SRC-012-lfp-spray-drying.md`)
- arXiv: `{source_id}-arxiv-{arxiv_id}.md` (e.g. `SRC-042-arxiv-2401.12345.md`)
- PubMed: `{source_id}-pubmed-{pmid}.md` (e.g. `SRC-043-pubmed-39876543.md`)
- Patents: `{source_id}-patent-{number}.md` (e.g. `SRC-PAT-003-EP2360117B1.md`)
- Call documents: `CALL-{call-id}-{description}.{ext}` (e.g. `CALL-innovfund-2025-nzt-fiche.pdf`)
- Supporting docs: descriptive filename (e.g. `dt-lfp-deep-dive-report.pdf`)
- Manual uploads: any descriptive filename

### How raw/ is used
- During `/wiki ingest`, the orchestrator checks `wiki/raw/` for full text matching each evidence source — if found, it produces a richer source page with more detailed findings
- During `/wiki query`, if a source page's extract is too thin, the raw file can be re-read for deeper context
- Future projects' retrievers check `wiki/raw/` before re-downloading a known source
- Call parser checks `wiki/raw/CALL-*` before re-parsing a known call document

## Ingest workflow (from completed project run)

1. Read the project's `evidence_store.jsonl` — create/update source pages (check `wiki/raw/` for full text to produce richer summaries)
2. Read `claim_registry.jsonl` — create/update claim pages (supported claims only)
3. Read `gap_analysis.json` — create/update gap pages
4. Extract entities from sources and `decision_log.jsonl` — create/update entity pages
5. Extract concepts from `sota_summary.md` — create/update concept pages
6. Read `call_brief.json` + `evaluation_matrix.json` — create/update funding call page
7. Update `index.md` with all new/updated pages
8. Update `overview.md` if the ingest meaningfully changes the big picture
9. Append to `log.md`
10. Deduplicate: sources by DOI/title match, claims by semantic similarity (confirm with user)

## Query workflow

1. Read `index.md` to find relevant pages
2. Read those pages fully
3. Synthesize an answer with citations: `(source: [[sources/SRC-xxx-title]])`
4. Offer to save the answer as a new analysis page if it synthesizes across multiple sources

## Integration with ProposalWriter agents

### Research Phase 0 (wiki check)
Before spawning retrievers, the research orchestrator:
1. Reads `wiki/index.md` to find relevant source/claim/gap pages
2. Imports relevant wiki claims into project-local `claim_registry.jsonl` (prefixed `WIKI-CLM-xxx`)
3. Imports relevant wiki sources into project-local `evidence_store.jsonl` (prefixed `WIKI-SRC-xxx`)
4. Passes wiki context to retrievers and synthesizers

### Retrievers
Before searching, retrievers check the wiki for existing sources in this domain.
- Skip searches for topics already well-covered
- Focus on gaps the wiki flags as open

### Synthesizers
- Read `wiki/overview.md` and relevant concept pages as baseline context
- Read `wiki/pages/gaps/` and `wiki/pages/entities/` for landscape intelligence

### Writers
- Read `wiki/pages/claims/` for pre-validated claim language
- Read `wiki/pages/concepts/` for consistent terminology
- Cite from project-local stores only (wiki claims imported during Phase 0)

## Log format
`## [YYYY-MM-DD] {operation} | {title}`

Operations: `setup`, `ingest`, `query`, `lint`, `update`
