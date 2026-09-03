"""figures: parse the figure register -> classify -> render in parallel (max 4) -> index."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from agency.domain.graph import NodeType
from agency.domain.models import FigureBatch
from agency.domain.runs import JobKind
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.jobs import handler, stage

PLOT_TYPES = {"sankey", "gantt", "heatmap", "curve", "bar", "pie", "map", "flow", "schematic"}
CONCEPT_WORDS = ("fal", "flux", "ideogram", "recraft", "illustrator", "figma", "concept", "hero", "cover")


def plan_figures(ctx: RunContext) -> StagePlan:
    return StagePlan("figures", [
        JobSpec("preflight", "figures.preflight", kind=JobKind.CODE),
        JobSpec("render", "figures.render", kind=JobKind.AGENT, deps=["preflight"], contract="plot_renderer"),
        JobSpec("index", "figures.index", kind=JobKind.CODE, deps=["render"]),
        JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=["index"]),
    ])


stage(StageDef(name="figures", state_key="figures", planner=plan_figures, scope_key="figures",
               description="Render every figure in the figures register: data plots via Matplotlib/Plotly, concept "
                           "graphics via Fal.ai; four at a time.",
               flags={"only": "comma list of figure ids", "plots_only": "skip Fal.ai figures", "fal_only": "only Fal.ai figures",
                      "force": "re-render figures already marked final"}))


def parse_register(md: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in md.splitlines():
        if not line.strip().startswith("|"):
            header = None if header and rows else header
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if any("figure" in c.lower() or c.lower() in ("id", "fig") for c in cells):
                header = [re.sub(r"[^a-z]+", "_", c.lower()).strip("_") for c in cells]
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        row = {header[i] if i < len(header) else f"col{i}": v for i, v in enumerate(cells)}
        fid = next((v for v in row.values() if re.fullmatch(r"F-\d{2}", v)), None)
        if fid:
            row["figure_id"] = fid
            rows.append(row)
    return rows


def classify(row: dict[str, str]) -> tuple[str, str]:
    text = " ".join(row.values()).lower()
    tool = (row.get("tool") or row.get("generator") or "").lower()
    ftype = (row.get("type") or "").lower()
    if any(w in tool for w in CONCEPT_WORDS) or ftype == "concept" or (not ftype and any(w in text for w in ("concept graphic", "hero"))):
        return "concept_image_generator", ftype or "concept"
    for t in PLOT_TYPES:
        if t in ftype or t in text:
            return "plot_renderer", t
    return "plot_renderer", ftype or "other"


@handler("figures.preflight")
async def preflight(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    doc = rt.graph.document("figures_register")
    reg = rt.project_dir / "drafts" / "figures_register.md"
    md = doc.data.get("body", "") if doc else (reg.read_text() if reg.exists() else "")
    if not md.strip():
        raise JobFailed("no figures register (drafts/figures_register.md); writers or the review loop create it")
    rows = parse_register(md)
    if not rows:
        raise JobFailed("figures register has no rows with F-xx ids")
    only = {x.strip() for x in str(rt.flags.get("only", "")).split(",") if x.strip()}
    existing = {f.data.get("figure_id"): f for f in rt.graph.nodes(NodeType.FIGURE)}
    plan = []
    skipped = []
    for r in rows:
        fid = r["figure_id"]
        if only and fid not in only:
            continue
        contract, ftype = classify(r)
        if rt.flags.get("plots_only") and contract != "plot_renderer":
            continue
        if rt.flags.get("fal_only") and contract != "concept_image_generator":
            continue
        if "pending" in " ".join(r.values()).lower() and "cfo" in " ".join(r.values()).lower():
            skipped.append(f"{fid}: pending CFO data")
            continue
        prev = existing.get(fid)
        if prev and prev.data.get("status") == "final" and not rt.flags.get("force"):
            skipped.append(f"{fid}: already final")
            continue
        if contract == "concept_image_generator" and not rt.ws.config.secrets.get("FAL_KEY"):
            skipped.append(f"{fid}: FAL_KEY not set")
            continue
        plan.append({"figure_id": fid, "contract": contract, "type": ftype, "row": r})
    (rt.project_dir / "figures" / "scripts").mkdir(parents=True, exist_ok=True)
    return {"plan": plan, "skipped": skipped, "summary": f"{len(plan)} figures to render, {len(skipped)} skipped"}


async def render_one(rt: JobRuntime, item: dict[str, Any], sem: asyncio.Semaphore) -> dict[str, Any]:
    async with sem:
        fid, contract, ftype, row = item["figure_id"], item["contract"], item["type"], item["row"]
        model = None
        if contract == "plot_renderer":
            model = rt.ws.config.models["fast"] if ftype in ("bar", "pie", "curve") else rt.ws.config.models["balanced"]
            if ftype == "schematic":
                model = rt.ws.config.models["reasoning"]
        out_png = rt.project_dir / "figures" / f"{fid}.png"
        res = await rt.agent(contract, phase=f"render:{fid}", output_model=FigureBatch, allowed_writes=set(),
                             model_override=model,
                             inputs=[("figures register", str(rt.project_dir / "drafts" / "figures_register.md")),
                                     ("drafts (data sources)", str(rt.project_dir / "drafts")),
                                     ("financial tables", str(rt.project_dir / "intermediate" / "financial_tables.json")),
                                     ("evidence store", str(rt.project_dir / "memory" / "evidence_store.jsonl"))],
                             instructions=f"Render figure {fid} only. Register row: {json.dumps(row)}\nType: {ftype}. "
                                          f"Write the image to `{out_png}` (and the script to figures/scripts/{fid}.py for plots). "
                                          f"Return a `FigureBatch` with one FigureSpec (figure_id {fid}, output_path relative to "
                                          "project_dir, status 'draft' or 'tbd' if data is missing — never invent data).")
        batch = FigureBatch.model_validate(res.structured)
        spec = next((f for f in batch.figures if f.figure_id == fid), batch.figures[0] if batch.figures else None)
        if spec is None:
            raise JobFailed(f"{fid}: no figure spec returned")
        data = spec.model_dump(mode="json", exclude_none=True)
        png = rt.project_dir / (spec.output_path or f"figures/{fid}.png")
        if png.exists():
            data["blob"] = rt.ws.blobs.put_file(png)
            data["output_path"] = str(png.relative_to(rt.project_dir))
        elif spec.status not in ("tbd",):
            data["status"] = "tbd"
            data["notes"] = (data.get("notes") or "") + " [engine: image file not found]"
        existing = next((f for f in rt.graph.nodes(NodeType.FIGURE) if f.data.get("figure_id") == fid), None)
        if existing:
            existing.data.update(data)
            existing.created_by = rt.job.id
            node = rt.graph.store.put_node(existing)
        else:
            node = rt.graph.add(NodeType.FIGURE, data, id=fid, created_by=rt.job.id)
        (rt.project_dir / "figures" / f"{fid}.json").write_text(json.dumps(data, indent=2))
        return {"figure_id": fid, "status": data.get("status"), "node_id": node.id}


@handler("figures.render")
async def render(rt: JobRuntime) -> dict[str, Any]:
    plan = rt.result_of("preflight")["plan"]
    if not plan:
        return {"summary": "nothing to render", "results": []}
    sem = asyncio.Semaphore(4)
    results = await asyncio.gather(*(render_one(rt, item, sem) for item in plan), return_exceptions=True)
    ok = [r for r in results if not isinstance(r, Exception)]
    errors = [str(r) for r in results if isinstance(r, Exception)]
    if not ok and errors:
        raise JobFailed("; ".join(errors))
    return {"results": ok, "errors": errors,
            "summary": f"{sum(1 for r in ok if r['status'] != 'tbd')} rendered, {sum(1 for r in ok if r['status'] == 'tbd')} tbd"
                       + (f", {len(errors)} failed" if errors else "")}


@handler("figures.index")
async def index(rt: JobRuntime) -> dict[str, Any]:
    figs = sorted(rt.graph.nodes(NodeType.FIGURE), key=lambda n: n.data.get("figure_id", ""))
    idx = {"figures": [f.data for f in figs], "count": len(figs)}
    (rt.project_dir / "figures" / "index.json").write_text(json.dumps(idx, indent=2, default=str))
    doc = rt.graph.document("figures_register")
    if doc:
        body = doc.data.get("body", "")
        for f in figs:
            fid, status = f.data.get("figure_id"), f.data.get("status", "draft")
            body = re.sub(rf"(\|\s*{fid}\s*\|[^\n]*)\|\s*(tbd|in_progress|draft|final)\s*\|", rf"\1| {status} |", body)
        rt.graph.put_document("figures_register", doc.data.get("title", "Figures register"), body, created_by=rt.job.id)
    rt.ctx.materialize()
    return {"count": len(figs), "summary": f"index.json with {len(figs)} figures"}
