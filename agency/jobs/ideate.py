"""ideate: interview -> candidate framings -> shallow prior-art probes -> evaluator -> user choice."""
from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from agency.domain.graph import NodeType
from agency.domain.models import EvidenceResult, IdeationBrief
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_evidence
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage
from agency.jobs.common import replace_hypothesis


def plan_ideate(ctx: RunContext) -> StagePlan:
    return StagePlan("ideate", [
        JobSpec("setup", "ideate.setup", kind=JobKind.CODE),
        JobSpec("interview", "ideate.interview", kind=JobKind.SESSION, deps=["setup"], contract="idea_interviewer"),
        JobSpec("probe_and_evaluate", "ideate.probe_evaluate", kind=JobKind.AGENT, deps=["interview"], contract="idea_evaluator"),
        JobSpec("choose", "ideate.choose", kind=JobKind.INBOX, deps=["probe_and_evaluate"]),
        JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=["choose"]),
    ])


stage(StageDef(name="ideate", state_key="ideation", planner=plan_ideate, interactive=True,
               description="Develop the idea with you: interview, candidate framings, shallow prior-art probes, "
                           "comparative scoring, and a chosen hypothesis written into the context. Without a parsed "
                           "call this is exploratory: the hypothesis is marked preliminary and parse-call aligns it later.",
               flags={"max_loops": "max rework loops (default 2)", "probe_sources": "sources per probe (default 8)"}))


@handler("ideate.setup")
async def setup(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    ctx = rt.context_document()
    hyp = (ctx.get("hypothesis") or "").strip()
    if hyp and "to be completed" not in hyp.lower():
        ans = await rt.ask(f"The project already has a hypothesis:\n\n“{hyp}”\n\nRe-open it for ideation?",
                           ["yes, refine it", "no, keep it and skip ideation"], header="Ideation", key="reopen")
        if str(ans.get("choice", "")).startswith("no"):
            raise JobFailed("ideation skipped by user (hypothesis kept)")
    return {"summary": "ideation setup", "existing_hypothesis": hyp}


@handler("ideate.interview")
async def interview(rt: JobRuntime) -> dict[str, Any]:
    project = rt.ws.get_project(rt.project_id)
    ctx = rt.context_document()
    opening = f"""Run the ideation interview for project "{project.name}".
Known so far — funder: {project.funder or 'unknown'}; instrument: {project.mechanism or 'unknown'}; topic: {project.topic or '-'};
current hypothesis: {ctx.get('hypothesis') or 'none'}.
Follow your protocol one batch at a time: ask each batch with the AskUserQuestion tool (or plain text; the
researcher answers through the inbox). Record answers verbatim. When you have enough, call
`mcp__agency__submit_result` with kind "framings" and payload {{"raw_idea": ..., "interview_notes": ..., "framings": [
{{"framing_id": "FRM-001", "statement": ..., "mechanism": ..., "novelty_type": ..., "target_gap": ..., "closest_competitor": ..., "reviewer_fear": ...}}, ...]}}
(2-3 framings), present them to the researcher for corrections, resubmit if they change anything, then call `finish`."""
    res = await rt.session("idea_interviewer", opening, until_kinds={"framings"}, header="Ideation interview",
                           max_user_turns=int(rt.flags.get("max_turns") or 25))
    payload = res.latest("framings") or {}
    framings = payload.get("framings") or []
    if not framings:
        raise JobFailed("the interview produced no framings")
    for i, f in enumerate(framings, 1):
        f.setdefault("framing_id", f"FRM-{i:03d}")
    notes = payload.get("interview_notes") or "\n\n".join(f"**{t['role']}**: {t['text']}" for t in res.transcript)
    rt.graph.put_document("ideation_notes", "Ideation interview notes", notes, created_by=rt.job.id,
                          raw_idea=payload.get("raw_idea", ""), framings=framings)
    return {"framings": framings, "raw_idea": payload.get("raw_idea", ""),
            "summary": f"{len(framings)} candidate framings from {res.user_turns} user turns"}


async def probe(rt: JobRuntime, framing: dict[str, Any], max_sources: int) -> dict[str, Any]:
    lo, hi = rt.reserve_ids("SRC", max_sources + 4)
    fid = framing["framing_id"]
    res = await rt.agent("literature_searcher", phase=f"probe:{fid}", output_model=EvidenceResult,
                         id_ranges={"SRC": (lo, hi)}, allowed_writes=set(), max_turns=40, budget_usd=1.5,
                         inputs=[("research context", str(rt.project_dir / "context.md")),
                                 ("existing evidence", str(rt.project_dir / "memory" / "evidence_store.jsonl"))],
                         instructions=f"""SHALLOW IDEATION PROBE — not full research. Framing {fid}:
"{framing.get('statement')}" — mechanism: {framing.get('mechanism')}; claimed novelty: {framing.get('novelty_type')};
closest competitor named by the researcher: {framing.get('closest_competitor') or 'none'}; reviewer fear: {framing.get('reviewer_fear') or 'none'}.
Find the {max_sources} closest pieces of prior art (max {max_sources} sources) and state in `summary` how close each comes
to the framing. Use `gaps` for what nobody seems to have done.""")
    result = EvidenceResult.model_validate(res.structured)
    ingested = ingest_evidence(rt.graph, result, retrieved_by="literature_searcher", job_id=rt.job.id, id_range=(lo, hi))
    doc = rt.graph.put_document(f"probe_{fid}", f"Prior-art probe {fid}", result.summary, created_by=rt.job.id,
                                framing_id=fid, sources=ingested["sources"] + ingested["duplicates"], gaps=result.gaps,
                                file=f"intermediate/ideation_probe_{fid}_results.json")
    rt.graph.update(doc, body=json.dumps(result.model_dump(mode="json"), indent=1))
    return {"framing_id": fid, "sources": ingested["sources"], "duplicates": ingested["duplicates"]}


async def evaluate(rt: JobRuntime, framings: list[dict[str, Any]], raw_idea: str, round_no: int) -> IdeationBrief:
    inputs = [("research context", str(rt.project_dir / "context.md")),
              ("interview notes", str(rt.project_dir / "intermediate" / "ideation_notes.md")),
              ("call spec (if any)", str(rt.project_dir / "intermediate" / "call_spec.json")),
              ("evidence store (probe sources)", str(rt.project_dir / "memory" / "evidence_store.jsonl"))]
    for f in framings:
        inputs.append((f"probe results {f['framing_id']}", str(rt.project_dir / "intermediate" / f"ideation_probe_{f['framing_id']}_results.json")))
    res = await rt.agent("idea_evaluator", phase=f"evaluate:r{round_no}", output_model=IdeationBrief, inputs=inputs,
                         allowed_writes=set(), instructions="Candidate framings:\n" + json.dumps(framings, indent=1, ensure_ascii=False)
                         + f"\nRaw idea: {raw_idea}\nScore every framing against its probe evidence; keep framing_ids; "
                           "set status 'draft' (the researcher chooses) or 'needs_rework' if none is fundable.")
    return IdeationBrief.model_validate(res.structured)


@handler("ideate.probe_evaluate")
async def probe_evaluate(rt: JobRuntime) -> dict[str, Any]:
    info = rt.result_of("interview")
    framings = info["framings"]
    n = int(rt.flags.get("probe_sources") or 8)
    probes = await asyncio.gather(*(probe(rt, f, n) for f in framings))
    brief = await evaluate(rt, framings, info.get("raw_idea", ""), round_no=1)
    node = rt.graph.add(NodeType.IDEATION_BRIEF, brief.model_dump(mode="json", exclude_none=True), created_by=rt.job.id)
    return {"brief_id": node.id, "probes": probes, "round": 1,
            "summary": f"{sum(len(p['sources']) for p in probes)} probe sources; recommendation: {brief.recommendation[:120]}"}


def _framing_label(f) -> str:
    sc = f.scores
    return f"{f.framing_id}: {f.statement[:90]} (novelty {sc.novelty_defensibility:g}, gap {sc.gap_alignment:g}, feas {sc.feasibility:g})"


@handler("ideate.choose")
async def choose(rt: JobRuntime) -> dict[str, Any]:
    info = rt.result_of("probe_and_evaluate")
    node = rt.graph.get(info["brief_id"])
    brief = IdeationBrief.model_validate(node.data)
    framings_raw = rt.result_of("interview")["framings"]
    max_loops = int(rt.flags.get("max_loops") or 2)
    loops = 0
    while True:
        options = [_framing_label(f) for f in brief.candidate_framings] + ["rework a framing", "abandon ideation"]
        ans = await rt.ask("Evaluator recommendation: " + (brief.recommendation or "(none)") +
                           f"\nStatus: {brief.status}. Choose the framing to commit to, or rework.",
                           options, header="Choose framing", key=f"choose_r{loops + 1}")
        choice = str(ans.get("choice") or ans.get("text") or "")
        if choice.startswith("abandon"):
            rt.graph.update(node, status="needs_rework")
            raise JobFailed("ideation abandoned by user")
        if choice.startswith("rework"):
            loops += 1
            if loops > max_loops:
                raise JobFailed("rework loop limit reached — the idea needs offline maturation")
            fix = await rt.ask("Which framing should change, and how? (free text: 'FRM-002: focus on …')", [],
                               header="Rework", key=f"rework_r{loops}")
            text = str(fix.get("text") or fix.get("choice") or "")
            m = re.match(r"\s*(FRM-\d+)\s*:?\s*(.*)", text, re.S)
            target = m.group(1) if m else (brief.candidate_framings[0].framing_id)
            changed = [f for f in framings_raw if f["framing_id"] == target]
            for f in changed:
                f["statement"] = (m.group(2).strip() if m and m.group(2).strip() else f["statement"])
                f["rework_note"] = text
            if changed:
                await asyncio.gather(*(probe(rt, f, int(rt.flags.get("probe_sources") or 8)) for f in changed))
            brief = await evaluate(rt, framings_raw, rt.result_of("interview").get("raw_idea", ""), round_no=loops + 1)
            node = rt.graph.add(NodeType.IDEATION_BRIEF, brief.model_dump(mode="json", exclude_none=True), created_by=rt.job.id)
            continue
        fid = choice.split(":")[0].strip()
        chosen = next((f for f in brief.candidate_framings if f.framing_id == fid), None)
        if chosen is None:
            chosen = brief.candidate_framings[0]
        break
    brief.chosen_framing_id = chosen.framing_id
    brief.status = "chosen"
    rt.graph.update(node, chosen_framing_id=chosen.framing_id, status="chosen")
    hyp = f"{chosen.statement}\n\n**Mechanism**: {chosen.mechanism}\n\n**Novelty type**: {chosen.novelty_type} — target gap: {chosen.target_gap}"
    replace_hypothesis(rt.graph, hyp, chosen.statement, created_by=rt.job.id,
                       concept_status="aligned" if rt.graph.callspec_node() is not None else "preliminary")
    rt.log_decision("Which project framing to pursue?", f"{chosen.framing_id}: {chosen.statement}",
                    [f"alternatives: {[f.framing_id for f in brief.candidate_framings if f.framing_id != chosen.framing_id]}",
                     brief.recommendation], type="framing_chosen", evidence_refs=chosen.closest_prior_art)
    rt.ctx.materialize()
    return {"chosen": chosen.framing_id, "loops": loops, "summary": f"chose {chosen.framing_id} after {loops} rework loop(s)"}
