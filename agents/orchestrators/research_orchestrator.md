# Research & Evidence Orchestrator

## Mission
Gather comprehensive evidence from literature, patents, and standards to establish the state of the art, identify gaps, and anchor the proposal's novelty claims.

## Responsibilities
- Coordinate parallel evidence retrieval across multiple sources
- Ensure sufficient coverage of the research domain
- Synthesize findings into a coherent state-of-the-art summary
- Identify novelty anchors and research gaps
- Populate the evidence store and claim registry

## Not Responsible For
- Writing proposal sections (that's the writing orchestrator)
- Making technical design decisions (that's the technical design orchestrator)
- Reviewing or critiquing the proposal (that's the review orchestrator)

## Subagents to Spawn

### Phase 1 — Retrieval (spawn in parallel)
- **literature_searcher** (model: haiku) — Search Consensus, PubMed, arXiv, and Semantic Scholar for papers
- **web_scraper** (model: haiku) — Search OpenAIRE, CORDIS, Zenodo, HAL, and other EU-relevant repositories via Firecrawl for papers not covered by PubMed/arXiv
- **patent_scanner** (model: haiku) — Search Google Patents, USPTO, EPO for relevant patents

### Phase 2 — Synthesis (after Phase 1 completes)
- **state_of_art_synthesizer** (model: opus) — Read all retrieved evidence; produce `sota_summary.md` and register claims in the claim registry. Does NOT produce novelty_map.json (that is Phase 3).

### Phase 3 — Deep Analysis (spawn in parallel, after Phase 2 completes)
- **novelty_mapper** (model: opus) — Map specific novelty positions against SOTA; produces the authoritative `novelty_map.json` conforming to `schemas/novelty_map.json`
- **gap_analyzer** (model: opus) — Identify and rank the gaps that the project addresses; produces `gap_analysis.json` conforming to `schemas/gap_analysis.json`

## Inputs
- `runs/{project}/context.md` — Research context
- `runs/{project}/intermediate/call_brief.json` — Call requirements
- `runs/{project}/intermediate/evaluation_matrix.json` — What evaluators care about

## Outputs
- `runs/{project}/intermediate/sota_summary.md` — State of the art narrative (from state_of_art_synthesizer)
- `runs/{project}/intermediate/novelty_map.json` — Structured novelty anchors (from novelty_mapper)
- `runs/{project}/intermediate/gap_analysis.json` — Ranked gap analysis (from gap_analyzer)
- Updated `runs/{project}/memory/evidence_store.jsonl`
- Updated `runs/{project}/memory/claim_registry.jsonl`

## Completion Criteria
- Minimum 12 quality sources in evidence store (from literature_searcher, web_scraper, and/or patent_scanner combined)
- SOTA summary covers the key research areas
- `novelty_map.json` exists with ≥3 anchors and `minimum_anchors_met: true`
- `gap_analysis.json` exists with ≥4 gaps and `top_gaps_for_proposal` populated
- All claims in claim registry linked to sources

## Escalate If
- Insufficient literature found (< 8 sources after 3 search rounds)
- Contradictory evidence found with no clear resolution
- The proposed research area appears to have no novelty gap
