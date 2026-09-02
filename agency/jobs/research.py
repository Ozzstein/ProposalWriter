"""research: knowledge-base import -> parallel retrieval -> SOTA -> novelty + gaps -> evidence gate."""
from __future__ import annotations

from typing import Any

from agency.domain.models import EvidenceResult, GapAnalysis, NoveltyMap, SotaOutput
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_claims, ingest_evidence, ingest_gaps, ingest_novelty
from agency.engine.plan import JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage

RETRIEVERS = [
    ("retrieve_literature", "literature_searcher", "literature"),
    ("retrieve_web", "web_scraper", "web repositories"),
    ("retrieve_patents", "patent_scanner", "patents"),
]


def plan_research(ctx: RunContext) -> StagePlan:
    jobs = [JobSpec("kb_import", "research.kb_import", kind=JobKind.CODE)]
    notes: list[str] = []
    retrievers = []
    for name, contract, label in RETRIEVERS:
        if contract == "web_scraper" and not ctx.ws.config.secrets.get("FIRECRAWL_API_KEY"):
            notes.append("web_scraper skipped: FIRECRAWL_API_KEY not set")
            continue
        only = ctx.flags.get("retrievers")
        if only and contract not in str(only):
            continue
        retrievers.append(name)
        jobs.append(JobSpec(name, "research.retrieve", kind=JobKind.AGENT, deps=["kb_import"], contract=contract,
                            params={"contract": contract, "label": label},
                            optional=contract in ("web_scraper", "patent_scanner")))
    jobs += [
        JobSpec("synthesize", "research.synthesize", kind=JobKind.AGENT, deps=retrievers, contract="state_of_art_synthesizer"),
        JobSpec("novelty", "research.novelty", kind=JobKind.AGENT, deps=["synthesize"], contract="novelty_mapper"),
        JobSpec("gaps", "research.gaps", kind=JobKind.AGENT, deps=["synthesize"], contract="gap_analyzer"),
        JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=["novelty", "gaps"], params={"gate": "evidence"}),
    ]
    return StagePlan(stage="research", jobs=jobs, notes=notes)


stage(StageDef(name="research", state_key="research", planner=plan_research, requires_gate="scope",
               requires_stages=("call_parsing",),
               description="Retrieve evidence in parallel, synthesise the state of the art, map novelty and gaps.",
               flags={"retrievers": "comma list to restrict (literature_searcher,web_scraper,patent_scanner)",
                      "focus": "extra search focus passed to every retriever"}))


@handler("research.kb_import")
async def kb_import(rt: JobRuntime) -> dict[str, Any]:
    try:
        from agency.kb.service import import_relevant
    except ImportError:  # knowledge base not built yet
        return {"summary": "knowledge base unavailable", "imported": 0}
    imported = import_relevant(rt.ws, rt.project_id, rt.topic(), job_id=rt.job.id)
    return {"summary": f"imported {imported.get('sources', 0)} sources, {imported.get('claims', 0)} claims from the knowledge base",
            **imported}


def _research_inputs(rt: JobRuntime) -> list[tuple[str, str]]:
    d = rt.project_dir
    return [("research context", str(d / "context.md")),
            ("call spec", str(d / "intermediate" / "call_spec.json")),
            ("existing evidence (dedupe against it)", str(d / "memory" / "evidence_store.jsonl")),
            ("existing claims", str(d / "memory" / "claim_registry.jsonl"))]


@handler("research.retrieve")
async def retrieve(rt: JobRuntime) -> dict[str, Any]:
    contract = rt.params["contract"]
    lo, hi = rt.reserve_ids("SRC", 40)
    focus = rt.flags.get("focus") or ""
    instructions = f"""Topic: {rt.topic()}
Find the strongest evidence for and against the project's central hypothesis, the closest prior art, and the
state of practice in {rt.params.get('label', 'your sources')}. Aim for 10-20 high-quality sources; quality beats
volume. Skip anything already in the existing evidence file. Give every source a `source_id` from your reserved
range, a real DOI/URL when one exists, and a specific `extract` (numbers, methods, limitations)."""
    if focus:
        instructions += f"\nAdditional focus from the researcher: {focus}"
    res = await rt.agent(contract, phase="retrieve", inputs=_research_inputs(rt), instructions=instructions,
                         output_model=EvidenceResult, id_ranges={"SRC": (lo, hi)}, allowed_writes=set())
    result = EvidenceResult.model_validate(res.structured)
    ingested = ingest_evidence(rt.graph, result, retrieved_by=contract, job_id=rt.job.id, id_range=(lo, hi))
    if result.gaps:
        rt.graph.put_document(f"retrieval_notes_{contract}", f"Retrieval notes — {contract}",
                              "\n".join(f"- {g}" for g in result.gaps) + "\n\nNext steps:\n" +
                              "\n".join(f"- {n}" for n in result.next_steps), created_by=rt.job.id)
    return {"sources": ingested["sources"], "duplicates": ingested["duplicates"], "claims": ingested["claims"],
            "summary": f"{len(ingested['sources'])} new sources ({len(ingested['duplicates'])} duplicates), "
                       f"{len(ingested['claims'])} candidate claims"}


@handler("research.synthesize")
async def synthesize(rt: JobRuntime) -> dict[str, Any]:
    lo, hi = rt.reserve_ids("CLM", 60)
    instructions = f"""Read every source in the evidence file and write the state-of-the-art narrative for:
{rt.topic()}
Return a `SotaOutput`: `summary_markdown` is the full narrative (sections: landscape, key approaches with
their limits, quantitative benchmarks, open problems, what the closest competitors do), 1500-4000 words,
citing sources inline as [SRC-xxx]. `claims` are the 10-30 statements writers will later cite: each with
`claim_id` from your reserved range, precise `text`, `type`, `supported_by` source ids, and `status`
('supported' only when at least one listed source backs it; otherwise 'assumption' or 'unsupported').
Do not write files; the engine persists the narrative and registers the claims."""
    res = await rt.agent("state_of_art_synthesizer", phase="synthesize", inputs=_research_inputs(rt),
                         instructions=instructions, output_model=SotaOutput, id_ranges={"CLM": (lo, hi)},
                         allowed_writes=set())
    out = SotaOutput.model_validate(res.structured)
    rt.graph.put_document("sota_summary", "State of the art", out.summary_markdown, created_by=rt.job.id,
                          key_areas=out.key_areas, thin_areas=out.thin_areas)
    claim_ids = ingest_claims(rt.graph, out.claims, owner="state_of_art_synthesizer", job_id=rt.job.id)
    return {"claims": claim_ids, "thin_areas": out.thin_areas,
            "summary": f"SOTA {len(out.summary_markdown.split())} words, {len(claim_ids)} claims registered"}


@handler("research.novelty")
async def novelty(rt: JobRuntime) -> dict[str, Any]:
    d = rt.project_dir
    inputs = _research_inputs(rt) + [("SOTA summary", str(d / "intermediate" / "sota_summary.md"))]
    res = await rt.agent("novelty_mapper", phase="novelty", inputs=inputs, output_model=NoveltyMap,
                         allowed_writes=set(), instructions=f"Project: {rt.topic()}\nUse anchor_ids NOV-001, NOV-002, … "
                         "Every anchor must cite source ids from the evidence file.")
    nm = NoveltyMap.model_validate(res.structured)
    ids = ingest_novelty(rt.graph, nm, job_id=rt.job.id)
    strong = sum(1 for a in nm.novelty_anchors if a.defensibility_score >= 6)
    return {"anchors": ids, "weak_points": nm.weak_points,
            "summary": f"{len(ids)} anchors ({strong} with defensibility >= 6); weak points: {len(nm.weak_points)}"}


@handler("research.gaps")
async def gaps(rt: JobRuntime) -> dict[str, Any]:
    d = rt.project_dir
    inputs = _research_inputs(rt) + [("SOTA summary", str(d / "intermediate" / "sota_summary.md"))]
    res = await rt.agent("gap_analyzer", phase="gaps", inputs=inputs, output_model=GapAnalysis, allowed_writes=set(),
                         instructions=f"Project: {rt.topic()}\nUse gap_ids GAP-001, GAP-002, … Rank "
                         "`top_gaps_for_proposal` by strategic importance under this call's criteria.")
    ga = GapAnalysis.model_validate(res.structured)
    ids = ingest_gaps(rt.graph, ga, job_id=rt.job.id)
    return {"gaps": ids, "top": ga.top_gaps_for_proposal,
            "summary": f"{len(ids)} gaps, top: {', '.join(ga.top_gaps_for_proposal[:3])}"}
