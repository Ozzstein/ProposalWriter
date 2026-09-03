"""finance: intake (files or form) -> financial model -> narrative sections -> financial red-team."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from agency.domain.graph import NodeType
from agency.domain.models import FinancialInputs, FinancialTables, ReviewBatch
from agency.domain.runs import JobKind
from agency.engine.materialize import ingest_claims, ingest_reviews
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage
from agency.jobs.drafting import draft_one

INPUTS_FILE = "intermediate/financial_model.json"


def plan_finance(ctx: RunContext) -> StagePlan:
    jobs = [JobSpec("intake", "finance.intake", kind=JobKind.INBOX),
            JobSpec("model", "finance.model", kind=JobKind.AGENT, deps=["intake"], contract="financial_modeler")]
    if not ctx.flags.get("model_only"):
        jobs.append(JobSpec("narrative", "finance.narrative", kind=JobKind.AGENT, deps=["model"], contract="financial_narrative_writer"))
        jobs.append(JobSpec("fin_review", "finance.review", kind=JobKind.AGENT, deps=["narrative"], contract="financial_reviewer"))
        last = "fin_review"
    else:
        last = "model"
    jobs.append(JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=[last]))
    return StagePlan("finance", jobs)


stage(StageDef(name="finance", state_key="finance", planner=plan_finance, interactive=True,
               requires_stages=("call_parsing",), scope_key="finance",
               description="Ingest CAPEX/OPEX/headcount/revenue/financing inputs, build the model, draft the financial "
                           "sections the call requires, and red-team hard-rejection thresholds.",
               flags={"model_only": "stop after the financial model", "sections": "comma list of financial section ids"}))


def _schema(rt: JobRuntime) -> dict[str, Any]:
    p = rt.ws.config.schemas_dir / "financial_inputs.json"
    return json.loads(p.read_text()) if p.exists() else FinancialInputs.model_json_schema()


def _validate(rt: JobRuntime, data: dict[str, Any]) -> list[str]:
    try:
        import jsonschema
        return [f"{'/'.join(map(str, e.absolute_path)) or '(root)'}: {e.message}"
                for e in jsonschema.Draft7Validator(_schema(rt)).iter_errors(data)][:10]
    except ImportError:  # pragma: no cover
        try:
            FinancialInputs.model_validate(data)
            return []
        except Exception as e:
            return [str(e)[:500]]


@handler("finance.intake")
async def intake(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    existing = rt.graph.document("financial_inputs")
    fdir = rt.project_dir / "inputs" / "financials"
    files = sorted(p for p in fdir.glob("*") if p.is_file()) if fdir.is_dir() else []
    data: dict[str, Any] | None = None
    source = ""
    if files:
        res = await rt.agent("financial_modeler", phase="ingest", output_model=FinancialInputs, allowed_writes=set(),
                             inputs=[("financial input files", str(fdir))] + [(p.name, str(p)) for p in files[:12]],
                             instructions="INGEST MODE: read the user's financial workbooks/notes and return a `FinancialInputs` "
                                          "object (meta, capex, opex, headcount, revenues, financing, working_capital, ghg_linkage, "
                                          "milestones). Amounts in the base currency; do not model anything yet; leave unknown "
                                          "values out rather than guessing.")
        data, source = res.structured, f"files: {', '.join(p.name for p in files)}"
    elif existing and existing.data.get("body"):
        data, source = json.loads(existing.data["body"]), "previous intake"
    errors = _validate(rt, data) if data else ["no financial inputs available"]
    attempts = 0
    while errors and attempts < 3:
        attempts += 1
        ans = await rt.form("Financial inputs", "Provide the financial inputs as JSON matching the schema "
                            "(or drop workbooks into inputs/financials/ and re-run)." +
                            (f"\n\nProblems with the current data: " + "; ".join(errors) if data else ""),
                            _schema(rt), key=f"financial_inputs_{attempts}", example=data or {})
        data = (ans.get("data") or {}) if isinstance(ans.get("data"), dict) else {}
        source = "inbox form"
        errors = _validate(rt, data) if data else ["empty submission"]
    if errors:
        raise JobFailed("financial inputs invalid: " + "; ".join(errors))
    body = json.dumps(data, indent=2)
    rt.graph.put_document("financial_inputs", "Financial inputs", body, created_by=rt.job.id, file=INPUTS_FILE, source=source)
    rt.log_decision("Financial inputs ingested", f"from {source}", ["schema-validated financial_inputs"], type="finance_ingest")
    rt.ctx.materialize()
    capex = data.get("capex", {}).get("total_by_scenario", {})
    return {"source": source, "summary": f"inputs from {source}; CAPEX scenarios: {capex or 'by category'}"}


@handler("finance.model")
async def model(rt: JobRuntime) -> dict[str, Any]:
    lo, hi = rt.reserve_ids("CLM", 30)
    spec = rt.ctx.callspec()
    hard = [r for r in (spec.requirements if spec else []) if r.kind == "hard_rule"]
    res = await rt.agent("financial_modeler", phase="model", output_model=FinancialTables, allowed_writes=set(),
                         id_ranges={"CLM": (lo, hi)},
                         inputs=[("financial inputs", str(rt.project_dir / INPUTS_FILE)),
                                 ("call spec", str(rt.project_dir / "intermediate" / "call_spec.json")),
                                 ("research context", str(rt.project_dir / "context.md"))],
                         instructions="Build the full model and return `FinancialTables`: `tables` (capex build-up, opex by "
                                      "year, headcount ramp, working capital, unit economics, cash flow, financing plan), "
                                      "`metrics` (payback, breakeven year, IRR/NPV if derivable, CER and GHG figures, FC and EiO "
                                      "dates), `markdown` (the human-readable tables), `claims` (CLM entries for every headline "
                                      "number writers will cite, type 'financial') and `hard_threshold_checks` for: " +
                                      ("; ".join(f"{r.id}: {r.text} [{r.rule}]" for r in hard) or "none defined") +
                                      ". You may write helper scripts under scratch/ with Bash.")
    out = FinancialTables.model_validate(res.structured)
    for old in rt.graph.nodes(NodeType.FINANCIAL_TABLE):
        rt.graph.set_status(old.id, "superseded")
    node = rt.graph.add(NodeType.FINANCIAL_TABLE, {"tables": out.tables, "metrics": out.metrics,
                                                   "checks": [c.model_dump(mode="json") for c in out.hard_threshold_checks]},
                        created_by=rt.job.id)
    rt.graph.put_document("financial_tables", "Financial tables", out.markdown, created_by=rt.job.id,
                          file="intermediate/financial_tables.md", metrics=out.metrics)
    rt.graph.put_document("financial_tables_json", "financial_tables.json", json.dumps({"tables": out.tables, "metrics": out.metrics}, indent=2),
                          created_by=rt.job.id, file="intermediate/financial_tables.json")
    claims = ingest_claims(rt.graph, out.claims, owner="financial_modeler", job_id=rt.job.id)
    _apply_checks(rt, out.hard_threshold_checks)
    rt.ctx.materialize()
    return {"node_id": node.id, "claims": claims, "metrics": out.metrics,
            "summary": f"model built: {len(out.tables)} tables, {len(claims)} financial claims, "
                       f"{sum(1 for c in out.hard_threshold_checks if not c.met)} threshold checks failing"}


def _apply_checks(rt: JobRuntime, checks) -> None:
    node = rt.graph.callspec_node()
    if node is None or not checks:
        return
    changed = False
    for r in node.data.get("requirements", []):
        for c in checks:
            if c.check_id == r.get("id") or (r.get("rule") and c.description and r["rule"].split()[0] in c.description):
                r["status"] = "met" if c.met else "unmet"
                changed = True
    if changed:
        rt.graph.store.put_node(node)
    for c in checks:
        if not c.met and c.hard_rejection_risk:
            rt.emit("escalation", severity="critical", reason="hard_threshold", details=[c.check_id, c.description, c.action_required])


@handler("finance.narrative")
async def narrative(rt: JobRuntime) -> dict[str, Any]:
    spec = rt.ctx.callspec()
    only = [x.strip() for x in str(rt.flags.get("sections", "")).split(",") if x.strip()]
    sections = [s for s in (spec.sections if spec else []) if s.kind == "financial" and (not only or s.id in only)]
    if not sections:
        return {"summary": "no financial sections in the CallSpec; nothing drafted", "sections": []}
    extra = ("Use ONLY numbers from intermediate/financial_tables.json (cite the financial CLM ids for every headline figure); "
             "never inline a number that is not in the tables.")
    results = await asyncio.gather(*(draft_one(rt, s, "financial_narrative_writer", extra=extra) for s in sections),
                                   return_exceptions=True)
    ok = [r for r in results if not isinstance(r, Exception)]
    errors = [str(r) for r in results if isinstance(r, Exception)]
    if not ok:
        raise JobFailed("; ".join(errors))
    return {"sections": [r["section_id"] for r in ok], "errors": errors,
            "summary": f"{len(ok)} financial sections drafted" + (f", {len(errors)} failed" if errors else "")}


@handler("finance.review")
async def review(rt: JobRuntime) -> dict[str, Any]:
    round_no = max((int(f.data.get("round", 0) or 0) for f in rt.graph.findings("financial")), default=0) + 1
    res = await rt.agent("financial_reviewer", phase="fin_review", output_model=ReviewBatch, allowed_writes=set(),
                         inputs=[("financial tables", str(rt.project_dir / "intermediate" / "financial_tables.json")),
                                 ("financial inputs", str(rt.project_dir / INPUTS_FILE)),
                                 ("drafts", str(rt.project_dir / "drafts")),
                                 ("call spec", str(rt.project_dir / "intermediate" / "call_spec.json")),
                                 ("claim registry", str(rt.project_dir / "memory" / "claim_registry.jsonl"))],
                         instructions="Return a `ReviewBatch` (reviewer_type 'financial' per financial section) plus "
                                      "`hard_rejection_checks` for every hard rule in the CallSpec and the internal "
                                      "consistency of narrative vs tables.")
    batch = ReviewBatch.model_validate(res.structured)
    ids = ingest_reviews(rt.graph, batch, reviewer_type="financial", round_no=round_no, job_id=rt.job.id)
    _apply_checks(rt, batch.hard_rejection_checks)
    risks = [c.check_id for c in batch.hard_rejection_checks if not c.met and c.hard_rejection_risk]
    if risks:
        await rt.ask(f"Hard-rejection risk detected: {risks}. Acknowledge to continue (the finance stage records this).",
                     ["acknowledged"], header="Escalation", key="fin_risk_ack")
        rt.log_decision("Hard-rejection risks acknowledged", ", ".join(risks), ["user acknowledged via inbox"], type="finance_risk_ack")
    return {"findings": ids, "risks": risks, "summary": f"{len(ids)} financial reports; hard-rejection risks: {risks or 'none'}"}
