"""external-feedback: ingest reviewer files -> triage (inbox) -> route to specialists -> apply patches."""
from __future__ import annotations

import asyncio
import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from agency.domain.graph import EdgeType, NodeType
from agency.domain.models import (ClaimBatch, EvidenceResult, FeedbackEntry, FeedbackParse, PatchBatch)
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_claims, ingest_evidence
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage

ROUTE_BY_CATEGORY = {
    "evidence": "literature_searcher",
    "technical": "state_of_art_synthesizer",
    "compliance": "compliance_checker",
    "writing": "feedback_applier",
    "style": "feedback_applier",
    "structural": "feedback_applier",
    "financial": "financial_reviewer",
    "business_plan": "bp_reviewer",
}
FINANCE_WORDS = re.compile(r"\b(capex|opex|wacc|npv|irr|dscr|cer|€/tco2|tco2|grant|equity|debt|offtake|payback|"
                           r"breakeven|cumulation|financial close|relevant cost|cost efficiency|clm-fin)\b", re.I)


def plan_feedback(ctx: RunContext) -> StagePlan:
    jobs = [JobSpec("resolve_round", "feedback.resolve", kind=JobKind.CODE)]
    # parse jobs are created dynamically inside `parse_all` (files are only known at run time)
    jobs += [
        JobSpec("parse_all", "feedback.parse_all", kind=JobKind.AGENT, deps=["resolve_round"], contract="feedback_parser"),
        JobSpec("ingest", "feedback.ingest", kind=JobKind.CODE, deps=["parse_all"]),
        JobSpec("triage", "feedback.triage", kind=JobKind.INBOX, deps=["ingest"]),
        JobSpec("dispatch", "feedback.dispatch", kind=JobKind.AGENT, deps=["triage"]),
        JobSpec("round_summary", "feedback.summary", kind=JobKind.CODE, deps=["dispatch"]),
        JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=["round_summary"], params={"gate": "external_feedback"}),
    ]
    return StagePlan(stage="external-feedback", jobs=jobs)


stage(StageDef(name="external-feedback", state_key="external_review", planner=plan_feedback, interactive=True,
               requires_stages=("writing",),
               description="Ingest external reviewer comments (files or pasted text), triage them with you, route "
                           "each to a specialist and apply the resulting patches.",
               flags={"new_round": "start a new round folder", "round": "work in round N", "text": "pasted reviewer text"}))


def _rounds_dir(rt: JobRuntime) -> Path:
    d = rt.project_dir / "inputs" / "reviews"
    d.mkdir(parents=True, exist_ok=True)
    return d


@handler("feedback.resolve")
async def resolve(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    base = _rounds_dir(rt)
    rounds = sorted(int(p.name[5:]) for p in base.glob("round*") if p.name[5:].isdigit())
    if rt.flags.get("round"):
        round_no = int(rt.flags["round"])
    elif str(rt.flags.get("new_round", "")).lower() in ("true", "1", "yes") or not rounds:
        round_no = (rounds[-1] + 1) if rounds else 1
    else:
        round_no = rounds[-1]
    rdir = base / f"round{round_no}"
    rdir.mkdir(exist_ok=True)
    text = rt.flags.get("text")
    if isinstance(text, str) and text.strip():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        (rdir / f"chat_{stamp}.md").write_text(text)
    known = {f.data.get("source_file") for f in rt.graph.feedback()}
    files = sorted(p for p in rdir.iterdir() if p.is_file() and not p.name.startswith("."))
    new = [p for p in files if str(p.relative_to(rt.project_dir)) not in known]
    if not new:
        ans = await rt.form("Reviewer comments needed", f"No new reviewer files in inputs/reviews/round{round_no}/. "
                            "Paste the reviewer comments below (or upload files and re-run).",
                            {"type": "object", "properties": {"text": {"type": "string"}}}, key=f"feedback_text_r{round_no}")
        pasted = (ans.get("data") or {}).get("text") or ans.get("text") or ""
        if not pasted.strip():
            raise JobFailed("no reviewer input provided")
        p = rdir / f"chat_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.md"
        p.write_text(pasted)
        new = [p]
    return {"round": round_no, "files": [str(p.relative_to(rt.project_dir)) for p in new],
            "summary": f"round {round_no}: {len(new)} new file(s)"}


@handler("feedback.parse_all")
async def parse_all(rt: JobRuntime) -> dict[str, Any]:
    info = rt.result_of("resolve_round")
    round_no = info["round"]
    entries: list[dict[str, Any]] = []

    async def one(rel: str) -> list[dict[str, Any]]:
        lo, hi = rt.reserve_ids("FBK", 40)
        res = await rt.agent("feedback_parser", phase=f"parse:{Path(rel).name}",
                             inputs=[("reviewer file", str(rt.project_dir / rel)),
                                     ("drafts (to locate comments)", str(rt.project_dir / "drafts")),
                                     ("outline", str(rt.project_dir / "intermediate" / "proposal_outline.md"))],
                             output_model=FeedbackParse, id_ranges={"FBK": (lo, hi)}, allowed_writes=set(),
                             instructions=f"Round {round_no}. source_file must be `{rel}`. Return a `FeedbackParse` "
                                          "with one FeedbackEntry per distinct reviewer comment (status 'open').")
        out = FeedbackParse.model_validate(res.structured)
        rows = []
        for e in out.entries:
            d = e.model_dump(mode="json", exclude_none=True)
            d["source_file"] = rel
            d["round"] = round_no
            rows.append(d)
        return rows

    results = await asyncio.gather(*(one(rel) for rel in info["files"]), return_exceptions=True)
    failed = []
    for rel, r in zip(info["files"], results):
        if isinstance(r, Exception):
            failed.append(f"{rel}: {r}")
        else:
            entries += r
    if failed and not entries:
        raise JobFailed("; ".join(failed))
    return {"entries": entries, "failed": failed, "summary": f"{len(entries)} comments parsed" + (f", {len(failed)} files failed" if failed else "")}


@handler("feedback.ingest")
async def ingest(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("resolve_round")["round"]
    existing = {f.data.get("dedupe_key"): f for f in rt.graph.feedback()}
    added, skipped = [], []
    for raw in rt.result_of("parse_all")["entries"]:
        key = raw.get("dedupe_key") or f"{raw.get('reviewer', '')}|{raw.get('location', '')}|{raw.get('comment', '')[:40]}"
        raw["dedupe_key"] = key
        prev = existing.get(key)
        if prev and prev.data.get("status") in ("rejected", "resolved", "ack"):
            skipped.append(prev.id)
            continue
        cat = raw.get("category", "ambiguous")
        raw.setdefault("routed_to", ROUTE_BY_CATEGORY.get(cat))
        if cat == "ack":
            raw["status"] = "ack"
        elif cat == "parse_error":
            raw["status"] = "parse_error"
        else:
            raw["status"] = "open"
        if FINANCE_WORDS.search(raw.get("comment", "")) and cat in ("technical", "evidence", "writing"):
            raw["routed_to"] = "financial_reviewer"
        raw.pop("feedback_id", None)
        node = rt.graph.add(NodeType.FEEDBACK, raw, created_by=rt.job.id)
        added.append(node.id)
        existing[key] = node
    rt.ctx.materialize()
    return {"added": added, "skipped": skipped, "round": round_no,
            "summary": f"{len(added)} new comments logged, {len(skipped)} duplicates of closed items"}


def _open_items(rt: JobRuntime, round_no: int, statuses=("open",)) -> list:
    return [f for f in rt.graph.feedback() if int(f.data.get("round", 0)) == round_no and f.data.get("status") in statuses]


@handler("feedback.triage")
async def triage(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("resolve_round")["round"]
    items = _open_items(rt, round_no)
    if not items:
        return {"approved": [], "summary": "nothing to triage"}
    # ambiguous items: ask which category applies
    for f in items:
        if f.data.get("category") == "ambiguous":
            cands = f.data.get("candidates") or list(ROUTE_BY_CATEGORY)
            ans = await rt.ask(f"{f.id}: how should this comment be classified?\n\n“{f.data.get('comment', '')[:400]}”",
                               cands, header="Classify", key=f"classify_{f.id}")
            cat = ans.get("choice") or ans.get("text") or cands[0]
            if cat in ROUTE_BY_CATEGORY:
                rt.graph.update(f, category=cat, routed_to=ROUTE_BY_CATEGORY[cat])
    items = _open_items(rt, round_no)
    rows = [{"id": f.id, "summary": f"[{f.data.get('category')} → {f.data.get('routed_to')}] "
                                    f"{f.data.get('location') or '?'}: {f.data.get('comment', '')[:160]}"} for f in items]
    ans = await rt.approve(f"Triage round {round_no}", "Approve the comments to act on now; defer or skip the rest.",
                           rows, decisions=["approve", "defer", "skip"], key=f"triage_r{round_no}")
    decisions = ans.get("rows") or {}
    default = "approve" if ans.get("decision") in ("approve", "custom", None) else ans.get("decision")
    approved = []
    for f in items:
        d = decisions.get(f.id, default)
        if d == "approve":
            rt.graph.update(f, status="in_progress")
            approved.append(f.id)
        elif d == "defer":
            rt.graph.update(f, status="deferred", resolution=ans.get("note") or "deferred at triage")
        else:
            rt.graph.update(f, status="skipped", resolution=ans.get("note") or "skipped at triage")
    rt.log_decision(f"Triage of external review round {round_no}", f"{len(approved)} approved of {len(items)}",
                    [ans.get("note") or "inbox triage"], type="feedback_triage")
    return {"approved": approved, "summary": f"{len(approved)}/{len(items)} approved"}


def _target_section(rt: JobRuntime, f) -> str | None:
    spec = rt.ctx.callspec()
    loc = (f.data.get("location") or "").lower()
    if not loc or not spec:
        return None
    for s in spec.sections:
        if re.search(rf"(section|§)\s*{re.escape(s.id)}\b", loc) or loc.startswith(s.id + " ") or loc.startswith(s.id + "."):
            return s.id
    for s in spec.sections:
        if s.title.lower() in loc:
            return s.id
    return None


async def _resolve_targets(rt: JobRuntime, items: list) -> dict[str, str | None]:
    spec = rt.ctx.callspec()
    drafted = {s.data.get("section_id") for s in rt.graph.sections()}
    out: dict[str, str | None] = {}
    for f in items:
        sid = _target_section(rt, f)
        if sid is None and f.data.get("routed_to") in ("feedback_applier", "compliance_checker", "financial_reviewer"):
            options = [f"{s.id} {s.title}" for s in spec.sections if s.id in drafted][:6] + ["unlocatable"]
            ans = await rt.ask(f"Which section does {f.id} refer to?\n\n“{f.data.get('comment', '')[:300]}”"
                               f"\n(location given: {f.data.get('location') or 'none'})", options, header="Locate",
                               key=f"locate_{f.id}")
            choice = str(ans.get("choice") or ans.get("text") or "")
            sid = choice.split(" ")[0] if choice and choice != "unlocatable" else None
            if sid is None:
                rt.graph.update(f, status="unlocatable", resolution="section could not be identified")
        out[f.id] = sid
    return out


def _section_file(rt: JobRuntime, sid: str) -> tuple[Any, Path] | None:
    node = rt.graph.section(sid)
    if node is None:
        return None
    return node, rt.project_dir / "drafts" / (node.data.get("path") or f"{sid}.md")


def apply_patches(rt: JobRuntime, patches: list, round_no: int) -> dict[str, list[str]]:
    applied, stale = [], []
    for p in patches:
        target = Path(p.target_file).stem
        node = next((s for s in rt.graph.sections()
                     if Path(s.data.get("path", "")).stem == target or s.data.get("section_id") == target
                     or s.id == p.target_file), None)
        if node is None:
            stale.append(f"{p.feedback_id}: target {p.target_file} not found")
            continue
        text = node.data.get("draft_text", "")
        if p.old_text and p.old_text in text:
            new_text = text.replace(p.old_text, p.new_text, 1)
        elif p.old_text and re.sub(r"\s+", " ", p.old_text).strip() in re.sub(r"\s+", " ", text):
            norm = re.sub(r"\s+", " ", p.old_text).strip()
            pattern = re.compile(r"\s+".join(re.escape(w) for w in norm.split(" ")))
            new_text = pattern.sub(lambda m: p.new_text, text, count=1)
        elif not p.old_text:
            new_text = text.rstrip() + "\n\n" + p.new_text
        else:
            stale.append(f"{p.feedback_id}: old_text not found in {node.id}")
            continue
        node.data["draft_text"] = new_text
        node.data["word_count"] = len(new_text.split())
        node.created_by = rt.job.id
        rt.graph.store.put_node(node)
        pnode = rt.graph.add(NodeType.PATCH, p.model_dump(mode="json", exclude_none=True), created_by=rt.job.id)
        rt.graph.link(pnode, node, EdgeType.TARGETS, created_by=rt.job.id)
        if rt.graph.get(p.feedback_id):
            rt.graph.link(p.feedback_id, pnode, EdgeType.RESOLVED_BY, created_by=rt.job.id)
        applied.append(pnode.id)
    rt.ctx.materialize()
    return {"applied": applied, "stale": stale}


@handler("feedback.dispatch")
async def dispatch(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("resolve_round")["round"]
    items = _open_items(rt, round_no, statuses=("in_progress",))
    if not items:
        return {"summary": "nothing approved"}
    targets = await _resolve_targets(rt, items)
    items = [f for f in items if f.data.get("status") == "in_progress"]
    groups: dict[tuple[str, str | None], list] = {}
    for f in items:
        groups.setdefault((f.data.get("routed_to") or "feedback_applier", targets.get(f.id)), []).append(f)
    today = date.today().isoformat()
    outcomes: dict[str, str] = {}

    def close(f, status: str, resolution: str) -> None:
        rt.graph.update(f, status=status, resolution=resolution, resolved_at=today,
                        round_closed=round_no if status != "in_progress" else None)
        outcomes[f.id] = status

    async def patch_group(route: str, sid: str | None, group: list) -> None:
        sec = _section_file(rt, sid) if sid else None
        if sec is None:
            for f in group:
                close(f, "unlocatable", "no drafted section to patch")
            return
        node, path = sec
        entries = [{"feedback_id": f.id, **{k: f.data.get(k) for k in ("location", "original_text", "comment", "category")}}
                   for f in group]
        mode = ("PATCH MODE: for each comment decide whether the compliance issue is real against call_spec.json; "
                if route == "compliance_checker" else "")
        res = await rt.agent(route, phase=f"patch:{sid}", output_model=PatchBatch, allowed_writes={"Claim", "Source"},
                             inputs=[("target draft", str(path)), ("call spec", str(rt.project_dir / "intermediate" / "call_spec.json")),
                                     ("claim registry", str(rt.project_dir / "memory" / "claim_registry.jsonl")),
                                     ("evidence store", str(rt.project_dir / "memory" / "evidence_store.jsonl"))],
                             instructions=mode + f"Address these reviewer comments on `{path.name}` and return a `PatchBatch`; "
                                          f"`target_file` must be `{path.name}`, `old_text` verbatim from the draft.\n"
                                          + json.dumps(entries, ensure_ascii=False, indent=1),
                             extra={"Round": str(round_no)})
        batch = PatchBatch.model_validate(res.structured)
        if batch.new_sources:
            ingest_evidence(rt.graph, EvidenceResult(topic="feedback", summary="", sources=batch.new_sources),
                            retrieved_by=route, job_id=rt.job.id)
        if batch.new_claims:
            ingest_claims(rt.graph, batch.new_claims, owner=route, job_id=rt.job.id)
        result = apply_patches(rt, batch.patches, round_no)
        patched = {p.feedback_id for p in batch.patches}
        stale_ids = {s.split(":")[0] for s in result["stale"]}
        for f in group:
            if f.id in stale_ids:
                close(f, "stale", "patch old_text no longer matched the draft; review manually")
            elif f.id in patched:
                close(f, "resolved", f"patched {path.name}")
            elif f.id in batch.flagged_needs_evidence:
                close(f, "deferred", "needs new evidence; routed to literature next round")
            elif f.id in batch.flagged_needs_orchestrator:
                close(f, "deferred", "structural change requested; needs a redraft")
            else:
                close(f, "rejected", "specialist found no change needed")

    async def evidence_group(group: list) -> None:
        lo, hi = rt.reserve_ids("SRC", 20)
        comments = "\n".join(f"- {f.id}: {f.data.get('comment')} (re: {f.data.get('original_text') or '-'})" for f in group)
        res = await rt.agent("literature_searcher", phase="feedback:evidence", output_model=EvidenceResult,
                             id_ranges={"SRC": (lo, hi)}, allowed_writes=set(),
                             inputs=[("claim registry", str(rt.project_dir / "memory" / "claim_registry.jsonl")),
                                     ("evidence store", str(rt.project_dir / "memory" / "evidence_store.jsonl"))],
                             instructions="Find 1-3 high-quality sources per comment that support or refute the reviewer's "
                                          "concern:\n" + comments)
        ing = ingest_evidence(rt.graph, EvidenceResult.model_validate(res.structured), retrieved_by="literature_searcher",
                              job_id=rt.job.id, id_range=(lo, hi))
        for f in group:
            close(f, "resolved" if ing["sources"] else "deferred",
                  f"sources added: {', '.join(ing['sources'])}" if ing["sources"] else "no new evidence found")

    async def technical_group(group: list) -> None:
        comments = "\n".join(f"- {f.id}: {f.data.get('comment')} (re: {f.data.get('original_text') or '-'})" for f in group)
        res = await rt.agent("state_of_art_synthesizer", phase="feedback:technical", output_model=ClaimBatch,
                             allowed_writes=set(),
                             inputs=[("claim registry", str(rt.project_dir / "memory" / "claim_registry.jsonl")),
                                     ("evidence store", str(rt.project_dir / "memory" / "evidence_store.jsonl"))],
                             instructions="Assess each reviewer comment against the evidence. Return a `ClaimBatch` of "
                                          "corrected/added claims (empty if the reviewer is wrong):\n" + comments)
        ids = ingest_claims(rt.graph, ClaimBatch.model_validate(res.structured).claims, owner="state_of_art_synthesizer",
                            job_id=rt.job.id)
        for f in group:
            close(f, "resolved" if ids else "rejected", f"claims updated: {', '.join(ids)}" if ids else "reviewer concern not supported by evidence")

    tasks = []
    for (route, sid), group in groups.items():
        if route in ("feedback_applier", "compliance_checker", "financial_reviewer"):
            tasks.append(patch_group(route, sid, group))
        elif route == "literature_searcher":
            tasks.append(evidence_group(group))
        elif route == "state_of_art_synthesizer":
            tasks.append(technical_group(group))
        else:
            for f in group:
                close(f, "deferred", f"route {route} handled in the {route.split('_')[0]} stage")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    errors = [str(r) for r in results if isinstance(r, Exception)]
    for f in _open_items(rt, round_no, statuses=("in_progress",)):
        close(f, "deferred", "specialist failed: " + (errors[0][:200] if errors else "unknown"))
    counts: dict[str, int] = {}
    for s in outcomes.values():
        counts[s] = counts.get(s, 0) + 1
    return {"outcomes": outcomes, "errors": errors, "counts": counts,
            "summary": ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "no outcomes"}


@handler("feedback.summary")
async def summary(rt: JobRuntime) -> dict[str, Any]:
    round_no = rt.result_of("resolve_round")["round"]
    items = [f for f in rt.graph.feedback() if int(f.data.get("round", 0)) == round_no]
    counts: dict[str, int] = {}
    for f in items:
        counts[f.data.get("status", "?")] = counts.get(f.data.get("status", "?"), 0) + 1
    files = sorted({Path(p.data.get("target_file", "")).name for p in rt.graph.nodes(NodeType.PATCH)})
    lines = [f"## External Review — Round {round_no} Complete", "", "| Outcome | Count |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in sorted(counts.items())]
    changed = [f"- {f}" for f in files] or ["- none"]
    stale = [f"- {f.id}: {f.data.get('comment', '')[:120]}" for f in items if f.data.get("status") == "stale"] or ["- none"]
    lines += ["", "### Files changed", *changed, "", "### Stale items requiring manual review", *stale]
    rt.graph.put_document(f"feedback_summary_r{round_no}", f"External review round {round_no}", "\n".join(lines),
                          created_by=rt.job.id, round=round_no, counts=counts)
    return {"counts": counts, "summary": ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))}
