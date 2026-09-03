"""write-proposal: one writer job per CallSpec section; excellence first, abstract last."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agency.domain.callspec import CallSpec, SectionSpec
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_drafts, section_filename
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage

WRITER_BY_KIND = {
    "abstract": "abstract_writer",
    "excellence": "excellence_writer",
    "impact": "impact_writer",
    "implementation": "implementation_writer",
    "financial": "financial_narrative_writer",
}
IMPLEMENTATION_HINTS = ("work plan", "workplan", "implementation", "management", "consortium", "risk",
                        "timeline", "methodology", "approach", "resources", "milestone", "operational",
                        "technical maturity", "maturity")


def writer_for(section: SectionSpec) -> str | None:
    if section.kind in WRITER_BY_KIND:
        return WRITER_BY_KIND[section.kind]
    if section.kind in ("annex", "business_plan"):
        return None
    title = section.title.lower()
    if any(h in title for h in IMPLEMENTATION_HINTS):
        return "implementation_writer"
    if any(h in title for h in ("innovation", "excellence", "novelty", "state of the art", "objectives")):
        return "excellence_writer"
    return "impact_writer"


def draftable_sections(spec: CallSpec, only: list[str] | None = None, scope=None) -> list[tuple[SectionSpec, str]]:
    out = []
    for s in spec.sections:
        if not s.required:
            continue
        if only and s.id not in only:
            continue
        if s.kind == "financial" and scope is not None and scope.is_excluded("finance"):
            continue
        w = writer_for(s)
        if w is None:
            continue
        out.append((s, w))
    return out


def plan_write(ctx: RunContext) -> StagePlan:
    spec = ctx.callspec()
    if spec is None:
        raise JobFailed("no CallSpec — run parse-call first")
    only = [x.strip() for x in str(ctx.flags.get("sections", "")).split(",") if x.strip()] or None
    scope = ctx.scope()
    sections = draftable_sections(spec, only, scope)
    notes = [f"section {s.id} ({s.title}) skipped: finance excluded by scope"
             for s in spec.sections if s.kind == "financial" and s.required and scope is not None
             and scope.is_excluded("finance")]
    has_finance = ctx.graph.document("financial_tables") is not None or ctx.graph.nodes(
        __import__("agency.domain.graph", fromlist=["NodeType"]).NodeType.FINANCIAL_TABLE)
    jobs = [JobSpec("prepare", "draft.prepare", kind=JobKind.CODE)]
    excellence = [f"draft:{s.id}" for s, w in sections if w == "excellence_writer"]
    draft_jobs: list[str] = []
    for s, w in sections:
        if w == "financial_narrative_writer" and not has_finance:
            notes.append(f"section {s.id} ({s.title}) skipped: run finance first")
            continue
        if w == "abstract_writer":
            continue
        name = f"draft:{s.id}"
        deps = ["prepare"] + ([] if w == "excellence_writer" else excellence)
        jobs.append(JobSpec(name, "draft.section", kind=JobKind.AGENT, deps=deps, contract=w,
                            params={"section_id": s.id, "writer": w}))
        draft_jobs.append(name)
    abstract = next(((s, w) for s, w in sections if w == "abstract_writer"), None)
    last = draft_jobs or ["prepare"]
    if abstract:
        jobs.append(JobSpec(f"draft:{abstract[0].id}", "draft.section", kind=JobKind.AGENT, deps=list(last),
                            contract="abstract_writer", params={"section_id": abstract[0].id, "writer": "abstract_writer"}))
        last = [f"draft:{abstract[0].id}"]
    jobs.append(JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=list(last), params={"gate": "draft"}))
    return StagePlan(stage="write-proposal", jobs=jobs, notes=notes)


stage(StageDef(name="write-proposal", state_key="writing", planner=plan_write, requires_gate="evidence",
               requires_stages=("research",),
               description="Draft every required section from the graph: excellence first, then impact and "
                           "implementation in parallel, the abstract last.",
               flags={"sections": "comma list of section ids to (re)draft", "notes": "guidance passed to every writer"}))


@handler("draft.prepare")
async def prepare(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    spec = rt.ctx.callspec()
    sections = draftable_sections(spec, scope=rt.ctx.scope())
    return {"summary": f"{len(sections)} sections to draft", "sections": [s.id for s, _ in sections]}


def _section_inputs(rt: JobRuntime) -> list[tuple[str, str]]:
    d = rt.project_dir
    return [("research context", str(d / "context.md")),
            ("call spec (sections, criteria, requirements)", str(d / "intermediate" / "call_spec.json")),
            ("proposal outline", str(d / "intermediate" / "proposal_outline.md")),
            ("SOTA summary", str(d / "intermediate" / "sota_summary.md")),
            ("novelty map", str(d / "intermediate" / "novelty_map.json")),
            ("gap analysis", str(d / "intermediate" / "gap_analysis.json")),
            ("evidence store", str(d / "memory" / "evidence_store.jsonl")),
            ("claim registry", str(d / "memory" / "claim_registry.jsonl")),
            ("existing drafts", str(d / "drafts"))]


def section_instructions(rt: JobRuntime, spec: CallSpec, section: SectionSpec, fname: str,
                         extra: str = "") -> str:
    crits = [c for c in spec.criteria if c.id in section.criterion_ids]
    limit = (f"Word limit: {section.word_limit}." if section.word_limit else
             f"Page limit: {section.page_limit:g} pages (~{int(section.page_limit * 450)} words)." if section.page_limit else
             "No explicit limit; be dense and specific.")
    lines = [f"Draft section **{section.id}. {section.title}** (kind: {section.kind}) for `{spec.title}` "
             f"({spec.funder}, {spec.instrument or 'n/a'}).",
             f"Write the draft to `{rt.project_dir / 'drafts' / fname}` and its metadata to "
             f"`{rt.project_dir / 'drafts' / (Path(fname).stem + '_meta.json')}` (section_draft schema: "
             "section_name, draft_text (may be empty in the sidecar), claim_ids, source_ids, assumptions_used, "
             "open_issues, word_count). Start the file with `## {id}. {title}`.",
             limit]
    if section.guidance:
        lines.append(f"What the call requires here: {section.guidance}")
    if crits:
        lines.append("Criteria this section is scored on:")
        lines += [f"- {c.id} {c.name} (max {c.max_score:g}, weight {c.weight:g}): {c.text}" for c in crits]
    lines.append("Cite only claim IDs present in the claim registry and source IDs present in the evidence store; "
                 "mark anything else `[ASSUMPTION: …]` and list it in open_issues. Do not write other sections.")
    if rt.flags.get("notes"):
        lines.append(f"Researcher guidance: {rt.flags['notes']}")
    if extra:
        lines.append(extra)
    return "\n".join(lines)


async def draft_one(rt: JobRuntime, section: SectionSpec, writer: str, extra: str = "") -> dict[str, Any]:
    spec = rt.ctx.callspec()
    fname = section_filename(section.id, section.title)
    inputs = _section_inputs(rt)
    if writer == "abstract_writer":
        inputs.insert(0, ("all finished drafts (read them all)", str(rt.project_dir / "drafts")))
    instructions = section_instructions(rt, spec, section, fname, extra)
    attempt = 0
    while True:
        attempt += 1
        await rt.agent(writer, phase=f"draft:{section.id}", inputs=inputs, instructions=instructions,
                       allowed_writes={"Claim", "Decision"})
        ids = ingest_drafts(rt.graph, rt.project_dir, job_id=rt.job.id, section_ids=[section.id], callspec=spec)
        node = rt.graph.section(section.id)
        problems = []
        if not ids or node is None or not node.data.get("draft_text", "").strip():
            problems.append(f"no draft found at drafts/{fname}")
        else:
            unknown = rt.graph.unregistered_refs(node.data["draft_text"])
            if unknown:
                problems.append(f"draft cites unregistered ids: {sorted(unknown)}")
            if section.word_limit and node.data.get("word_count", 0) > section.word_limit * 1.15:
                problems.append(f"draft is {node.data['word_count']} words, limit {section.word_limit}")
        if not problems:
            return {"section_id": section.id, "node_id": node.id, "words": node.data.get("word_count"),
                    "claims": len(node.data.get("claim_ids", [])), "open_issues": node.data.get("open_issues", []),
                    "summary": f"{section.id} {section.title}: {node.data.get('word_count')} words, "
                               f"{len(node.data.get('claim_ids', []))} claims"}
        if attempt >= 2:
            raise JobFailed(f"section {section.id}: " + "; ".join(problems))
        instructions = section_instructions(rt, spec, section, fname, extra + "\n\n## Fix these problems from the "
                                            "previous attempt\n" + "\n".join(f"- {p}" for p in problems))


@handler("draft.section")
async def draft_section(rt: JobRuntime) -> dict[str, Any]:
    spec = rt.ctx.callspec()
    section = spec.section(rt.params["section_id"])
    if section is None:
        raise JobFailed(f"section {rt.params['section_id']} not in CallSpec")
    return await draft_one(rt, section, rt.params["writer"])
