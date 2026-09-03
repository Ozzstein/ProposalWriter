"""business-plan: discovery interview -> synthesis -> four writers -> red-team -> assembly."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from agency.domain.callspec import SectionSpec
from agency.domain.graph import NodeType
from agency.domain.models import ReviewBatch
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_drafts, ingest_reviews
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage

INTERVIEW_FILE = "intermediate/business_plan_interview.json"
FACTS_FILE = "intermediate/business_plan_facts.json"

BP_SECTIONS = [  # (section id, title, writer)
    ("BP-1", "Commercial: product, market, commercialisation, competition", "bp_commercial_writer"),
    ("BP-2", "Financial assumptions, cash flow, profitability, financing plan", "bp_financial_writer"),
    ("BP-3", "Counterparties and contracts", "bp_counterparty_writer"),
    ("BP-4", "Risk analysis and management", "bp_risk_writer"),
]


def plan_business_plan(ctx: RunContext) -> StagePlan:
    jobs = [JobSpec("prereq", "bp.prereq", kind=JobKind.CODE),
            JobSpec("interview", "bp.interview", kind=JobKind.SESSION, deps=["prereq"], contract="bp_interviewer"),
            JobSpec("synthesize", "bp.synthesize", kind=JobKind.AGENT, deps=["interview"], contract="bp_synthesizer")]
    for sid, title, writer in BP_SECTIONS:
        jobs.append(JobSpec(f"write:{sid}", "bp.write", kind=JobKind.AGENT, deps=["synthesize"], contract=writer,
                            params={"section_id": sid, "title": title, "writer": writer}))
    jobs += [JobSpec("bp_review", "bp.review", kind=JobKind.AGENT, deps=[f"write:{s[0]}" for s in BP_SECTIONS], contract="bp_reviewer"),
             JobSpec("assemble", "bp.assemble", kind=JobKind.CODE, deps=["bp_review"]),
             JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=["assemble"])]
    return StagePlan("business-plan", jobs)


stage(StageDef(name="business-plan", state_key="business_plan", planner=plan_business_plan, interactive=True,
               requires_stages=("call_parsing", "writing"),
               description="Assemble the business-plan annex: discovery interview, fact synthesis, commercial/financial/"
                           "counterparty/risk drafts, cross-artefact red-team, assembled document.",
               flags={"skip_interview": "reuse the saved interview without asking again"}))


@handler("bp.prereq")
async def prereq(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    spec = rt.ctx.callspec()
    if spec and not spec.needs_business_plan() and not rt.flags.get("force_bp"):
        ans = await rt.ask("The CallSpec lists no business-plan annex. Build one anyway?", ["yes", "no"],
                           header="Business plan", key="bp_needed")
        if str(ans.get("choice", "")).startswith("no"):
            raise JobFailed("business plan not required for this call")
    return {"summary": "prerequisites ok", "has_finance": rt.graph.document("financial_tables") is not None}


@handler("bp.interview")
async def interview(rt: JobRuntime) -> dict[str, Any]:
    saved = rt.graph.document("business_plan_interview")
    answers: dict[str, Any] = json.loads(saved.data["body"]) if saved and saved.data.get("body") else {"batches": {}}
    if rt.flags.get("skip_interview") and answers.get("batches"):
        return {"summary": "reused saved interview", "batches": sorted(answers["batches"])}
    done = sorted(answers.get("batches", {}))

    async def persist(sub: dict[str, Any]) -> None:
        if sub.get("kind") == "interview_batch":
            payload = sub.get("payload") or {}
            b = str(payload.get("batch") or len(answers["batches"]) + 1)
            answers["batches"][b] = payload
            rt.graph.put_document("business_plan_interview", "Business plan interview", json.dumps(answers, indent=2),
                                  created_by=rt.job.id, file=INTERVIEW_FILE)

    opening = f"""Run the business-plan discovery interview for project `{rt.project_id}` following your protocol,
batch by batch. Batches already answered (skip them): {done or 'none'}. Ask each batch with AskUserQuestion or
plain text; the researcher may answer 'defaults', 'skip' or 'pause'. After EVERY batch call
`mcp__agency__submit_result` with kind "interview_batch" and payload {{"batch": k, "theme": ..., "answers": [{{"question_id": ..., "answer": ..., "source": "user|default|skip|cfo"}}]}}.
When all batches are done (or the researcher pauses) call `finish` with the tally."""
    res = await rt.session("bp_interviewer", opening, header="Business-plan interview", on_submission=persist,
                           max_user_turns=int(rt.flags.get("max_turns") or 30))
    rt.ctx.materialize()
    return {"batches": sorted(answers.get("batches", {})), "summary": f"{len(answers.get('batches', {}))} batches saved"}


@handler("bp.synthesize")
async def synthesize(rt: JobRuntime) -> dict[str, Any]:
    target = rt.project_dir / FACTS_FILE
    await rt.agent("bp_synthesizer", phase="synthesize", allowed_writes={"Decision"},
                   inputs=[("interview answers", str(rt.project_dir / INTERVIEW_FILE)),
                           ("financial tables", str(rt.project_dir / "intermediate" / "financial_tables.json")),
                           ("drafts", str(rt.project_dir / "drafts")), ("call spec", str(rt.project_dir / "intermediate" / "call_spec.json")),
                           ("claim registry", str(rt.project_dir / "memory" / "claim_registry.jsonl")),
                           ("context", str(rt.project_dir / "context.md"))],
                   instructions=f"Write the consolidated facts JSON to `{target}` (every fact with a source_ref) and a "
                                f"gaps list to `{target.with_name('business_plan_gaps.md')}`. Mark CFO-scope facts explicitly.")
    if not target.exists():
        raise JobFailed(f"bp_synthesizer did not write {FACTS_FILE}")
    rt.graph.put_document("business_plan_facts", "Business plan facts", target.read_text(), created_by=rt.job.id, file=FACTS_FILE)
    gaps = target.with_name("business_plan_gaps.md")
    if gaps.exists():
        rt.graph.put_document("business_plan_gaps", "Business plan gaps", gaps.read_text(), created_by=rt.job.id,
                              file="intermediate/business_plan_gaps.md")
    return {"summary": f"facts JSON {target.stat().st_size // 1024} KB"}


@handler("bp.write")
async def write(rt: JobRuntime) -> dict[str, Any]:
    sid, title, writer = rt.params["section_id"], rt.params["title"], rt.params["writer"]
    fname = f"{sid.lower().replace('-', '_')}_{writer.replace('bp_', '').replace('_writer', '')}.md"
    target = rt.project_dir / "drafts" / fname
    await rt.agent(writer, phase=f"write:{sid}", allowed_writes={"Claim", "Decision"},
                   inputs=[("business plan facts", str(rt.project_dir / FACTS_FILE)),
                           ("interview answers", str(rt.project_dir / INTERVIEW_FILE)),
                           ("financial tables", str(rt.project_dir / "intermediate" / "financial_tables.json")),
                           ("proposal drafts", str(rt.project_dir / "drafts")),
                           ("claim registry", str(rt.project_dir / "memory" / "claim_registry.jsonl"))],
                   instructions=f"Write `{target}` (+ `{target.with_name(target.stem + '_meta.json')}` section_draft sidecar) "
                                f"covering: {title}. Every number must trace to the facts JSON or a CLM id; mark CFO-scope "
                                "items `[TO BE COMPLETED — CFO]`. Start with `## {sid}. {title}`.")
    if not target.exists():
        raise JobFailed(f"{writer} did not write {fname}")
    text = target.read_text()
    meta = {}
    mp = target.with_name(target.stem + "_meta.json")
    if mp.exists():
        try:
            meta = json.loads(mp.read_text())
        except json.JSONDecodeError:
            meta = {}
    data = {"section_id": sid, "section_name": title, "draft_text": text, "kind": "business_plan", "path": fname,
            "claim_ids": meta.get("claim_ids") or sorted(rt.graph.claim_refs(text)),
            "source_ids": meta.get("source_ids", []), "open_issues": meta.get("open_issues", []),
            "word_count": len(text.split())}
    existing = rt.graph.section(sid)
    if existing:
        existing.data.update(data)
        existing.status = "draft"
        node = rt.graph.store.put_node(existing)
    else:
        node = rt.graph.add(NodeType.SECTION, data, id=f"SEC-{sid}", status="draft", created_by=rt.job.id)
    cfo = text.count("[TO BE COMPLETED")
    return {"node_id": node.id, "cfo_markers": cfo, "summary": f"{sid}: {data['word_count']} words, {cfo} CFO markers"}


@handler("bp.review")
async def review(rt: JobRuntime) -> dict[str, Any]:
    round_no = max((int(f.data.get("round", 0) or 0) for f in rt.graph.findings("business_plan")), default=0) + 1
    res = await rt.agent("bp_reviewer", phase="bp_review", output_model=ReviewBatch, allowed_writes=set(),
                         inputs=[("BP drafts", str(rt.project_dir / "drafts")), ("facts", str(rt.project_dir / FACTS_FILE)),
                                 ("financial tables", str(rt.project_dir / "intermediate" / "financial_tables.json")),
                                 ("call spec", str(rt.project_dir / "intermediate" / "call_spec.json"))],
                         instructions="Return a `ReviewBatch` (reviewer_type 'business_plan', one report per BP section) "
                                      "covering numerical consistency, template coverage, CFO-marker hygiene and coherence with Part B.")
    batch = ReviewBatch.model_validate(res.structured)
    ids = ingest_reviews(rt.graph, batch, reviewer_type="business_plan", round_no=round_no, job_id=rt.job.id)
    return {"findings": ids, "summary": f"{len(ids)} BP reports; critical: {sum(1 for r in batch.sections for f in r.fixes if f.priority == 'critical')}"}


@handler("bp.assemble")
async def assemble(rt: JobRuntime) -> dict[str, Any]:
    parts = [rt.graph.section(sid) for sid, _, _ in BP_SECTIONS]
    parts = [p for p in parts if p]
    if not parts:
        raise JobFailed("no BP sections drafted")
    body = f"# Business Plan — {rt.ws.get_project(rt.project_id).name}\n\n" + "\n\n".join(p.data.get("draft_text", "") for p in parts)
    rt.graph.put_document("business_plan_assembled", "Business plan (assembled)", body, created_by=rt.job.id,
                          file="drafts/business_plan_assembled.md")
    rt.ctx.materialize()
    cfo = body.count("[TO BE COMPLETED")
    return {"cfo_markers": cfo, "words": len(body.split()), "summary": f"assembled {len(parts)} sections, {cfo} CFO markers open"}
