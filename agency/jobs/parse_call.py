"""parse-call: call document -> CallSpec (+ pack), outline, user approval, scope gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agency.domain.callspec import CallSpec, CriterionSpec, RequirementSpec, RequirementsBatch, SectionSpec
from agency.domain.graph import NodeType
from agency.domain.models import ConceptAlignment
from agency.domain.runs import JobKind
from agency.domain.scope import MODULES, MODULE_LABEL, STATES, ScopeConfig, apply_scope_change, hypothesis_of, rederive
from agency.engine.materialize import ingest_callspec
from agency.engine.plan import JobFailed, JobSpec, StageDef, StagePlan
from agency.engine.runtime import JobRuntime, RunContext
from agency.funders.packs import detect_pack
from agency.jobs import handler, stage
from agency.jobs.common import replace_hypothesis
from agency.legacy.importer import outline_to_sections

TEXT_SUFFIXES = {".txt", ".md", ".html", ".htm", ".json"}


SCOPE_HEADER = "Configure proposal scope"
ALIGN_HEADER = "Align the concept with the call"


def plan_parse_call(ctx: RunContext) -> StagePlan:
    if ctx.flags.get("scope_only") or ctx.flags.get("align_only"):
        if ctx.callspec() is None:
            raise JobFailed("parse the call first")
        if ctx.flags.get("align_only"):
            if ctx.ws.concept_status(ctx.project_id) != "preliminary":
                raise JobFailed("nothing to align: the concept is not preliminary")
            first = JobSpec("align_concept", "parse_call.align_concept", kind=JobKind.AGENT, contract="idea_evaluator")
        else:
            first = JobSpec("configure_scope", "parse_call.configure_scope", kind=JobKind.INBOX)
        return StagePlan("parse-call", [first, JobSpec("finalize", "finalize_stage", kind=JobKind.GATE,
                                                       deps=[first.name], params={"gate": "scope"})])
    jobs = [
        JobSpec("locate_inputs", "parse_call.locate", kind=JobKind.CODE),
        JobSpec("parse_call", "parse_call.parse", kind=JobKind.AGENT, deps=["locate_inputs"], contract="call_parser"),
        JobSpec("parse_eligibility", "parse_call.eligibility", kind=JobKind.AGENT, deps=["locate_inputs"],
                contract="eligibility_parser", optional=True),
        JobSpec("merge_spec", "parse_call.merge", kind=JobKind.CODE, deps=["parse_call", "parse_eligibility"]),
        JobSpec("approve_outline", "parse_call.approve", kind=JobKind.INBOX, deps=["merge_spec"]),
        JobSpec("configure_scope", "parse_call.configure_scope", kind=JobKind.INBOX, deps=["approve_outline"]),
    ]
    last = "configure_scope"
    if ctx.ws.concept_status(ctx.project_id) == "preliminary":
        jobs.append(JobSpec("align_concept", "parse_call.align_concept", kind=JobKind.AGENT,
                            deps=["configure_scope"], contract="idea_evaluator"))
        last = "align_concept"
    jobs.append(JobSpec("finalize", "finalize_stage", kind=JobKind.GATE, deps=[last], params={"gate": "scope"}))
    return StagePlan(stage="parse-call", jobs=jobs)


stage(StageDef(name="parse-call", state_key="call_parsing", planner=plan_parse_call, interactive=True,
               description="Parse the funding call into a CallSpec, build the outline, confirm with the user, "
                           "configure the proposal scope and align a preliminary concept with the call.",
               flags={"call_file": "path or name of the call document inside inputs/",
                      "template_file": "official application template to follow exactly",
                      "pack": "force a funder pack id (innovation-fund, horizon-europe-ria, nih-r01, nsf, generic)",
                      "scope_only": "only (re)configure the scope for an already parsed call",
                      "align_only": "only align a preliminary concept with the parsed call"}))


def _extract_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            return "\n\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as e:  # pragma: no cover - depends on the pdf
            return f"[pdf extraction failed: {e}]"
    if path.suffix.lower() == ".docx":
        try:
            import docx
            d = docx.Document(str(path))
            return "\n".join(p.text for p in d.paragraphs)
        except Exception as e:  # pragma: no cover
            return f"[docx extraction failed: {e}]"
    if path.suffix.lower() in TEXT_SUFFIXES:
        return path.read_text(errors="ignore")
    return ""


@handler("parse_call.locate")
async def locate(rt: JobRuntime) -> dict[str, Any]:
    rt.ctx.materialize()
    inputs = rt.project_dir / "inputs"
    inputs.mkdir(exist_ok=True)
    files = sorted(p for p in inputs.rglob("*") if p.is_file() and not p.name.endswith(".extracted.txt"))
    wanted = rt.flags.get("call_file")
    call_files = [p for p in files if not wanted or wanted in p.name or wanted == str(p)]
    call_files = [p for p in call_files if "review" not in str(p.relative_to(inputs)).lower()
                  and "financ" not in p.name.lower()]
    if not call_files:
        answer = await rt.form("Call document needed", "No call document was found in inputs/. Paste the call text "
                               "(or a URL you have already downloaded) below.",
                               {"type": "object", "properties": {"text": {"type": "string"}}}, key="call_text")
        text = (answer.get("data") or {}).get("text") or answer.get("text") or ""
        if not text.strip():
            raise JobFailed("no call document provided")
        target = inputs / "call_document.txt"
        target.write_text(text)
        key = rt.ws.blobs.put_file(target)
        rt.graph.add(NodeType.DOCUMENT, {"kind": "input", "title": target.name, "path": key,
                                         "relative": target.name}, created_by=rt.job.id)
        call_files = [target]
    extracted: list[str] = []
    for p in call_files:
        text = _extract_text(p)
        if text.strip():
            out = p.with_name(p.name + ".extracted.txt")
            out.write_text(text)
            extracted.append(str(out))
    template = rt.flags.get("template_file")
    template_files = [str(p) for p in files if (template and template in p.name) or "template" in p.name.lower()
                      or "part_b" in p.name.lower() or "part-b" in p.name.lower()]
    return {"call_files": [str(p) for p in call_files], "extracted": extracted, "template_files": template_files,
            "summary": f"{len(call_files)} call document(s), {len(template_files)} template(s)"}


@handler("parse_call.parse")
async def parse(rt: JobRuntime) -> dict[str, Any]:
    loc = rt.result_of("locate_inputs")
    project = rt.ws.get_project(rt.project_id)
    packs = rt.ctx.packs
    pack = packs.get(rt.flags.get("pack") or (project.settings or {}).get("pack") or "") or detect_pack(
        packs, project.funder, project.mechanism, *[Path(p).read_text(errors="ignore")[:20000] for p in loc.get("extracted", [])])
    inputs = [("call document", p) for p in loc.get("call_files", [])] + \
             [("extracted text", p) for p in loc.get("extracted", [])] + \
             [("official template (follow exactly)", p) for p in loc.get("template_files", [])]
    instructions = f"""Produce a complete `CallSpec` for this call.
- `pack` must be "{pack.id}" ({pack.name}).
- `sections`: every section the applicant must write, in template order, with `id` (e.g. "1", "1.2", "4.1b"),
  `title`, `kind` (abstract | excellence | impact | implementation | financial | business_plan | annex | other),
  page/word limits, `weight` (share of total score the section drives, 0-1, based on the criteria it serves),
  `criterion_ids` it addresses and 1-3 sentences of `guidance` from the call about what the section must contain.
- `criteria`: the evaluation criteria with `id` (C1, C2.1 …), `name`, `text`, `max_score`, `weight`, and
  `threshold` when the call defines minimum scores. If the call gives no weights, use max_score=5, weight=1.
- `requirements`: eligibility rules, hard rejection rules, format rules, annexes and deadlines. Mark
  `disqualifying: true` for anything that causes rejection. Put evaluable thresholds in `rule`
  (e.g. "cer_eur_per_tco2 <= 200").
- Fill `abstract_word_limit`, `total_page_limit`, `deadline`, `annexes`, `budget_rules` (funding rate,
  min/max grant, cost categories) whenever the call states them.
If an official template file is listed under inputs, its section structure takes precedence over the call text
and over any built-in outline. Read the extracted text files rather than the PDFs when both exist.
Do not copy the call document anywhere; archiving is handled by the engine."""
    if pack.criteria_hints:
        instructions += "\n\nKnown criteria for this funder (use unless the call contradicts them):\n" + \
            "\n".join(f"- {c['id']}: {c['name']} (max {c.get('max_score', 5)}, weight {c.get('weight', 1)})"
                      for c in pack.criteria_hints)
    res = await rt.agent("call_parser", phase="parse", inputs=inputs, instructions=instructions,
                         output_model=CallSpec, allowed_writes=set())
    spec = CallSpec.model_validate(res.structured)
    spec.pack = pack.id
    return {"callspec": spec.model_dump(mode="json"), "pack": pack.id,
            "summary": f"{len(spec.sections)} sections, {len(spec.criteria)} criteria, {len(spec.requirements)} requirements"}


@handler("parse_call.eligibility")
async def eligibility(rt: JobRuntime) -> dict[str, Any]:
    loc = rt.result_of("locate_inputs")
    inputs = [("call document", p) for p in loc.get("call_files", [])] + \
             [("extracted text", p) for p in loc.get("extracted", [])]
    res = await rt.agent("eligibility_parser", phase="eligibility", inputs=inputs, output_model=RequirementsBatch,
                         allowed_writes=set(), instructions=(
                             "Return a `RequirementsBatch`: every eligibility, compliance, deadline and hard-rule "
                             "requirement as a `RequirementSpec` (id, kind, text, rule, disqualifying, applies_to). "
                             "Set status to 'unknown' unless the call itself makes it not applicable."))
    batch = RequirementsBatch.model_validate(res.structured)
    return {"requirements": [r.model_dump(mode="json") for r in batch.requirements],
            "disqualifiers": batch.disqualifiers, "summary": f"{len(batch.requirements)} requirements"}


def _merge_requirements(spec: CallSpec, extra: list[dict[str, Any]], pack) -> None:
    seen = {r.id for r in spec.requirements}
    texts = {r.text.strip().lower() for r in spec.requirements}
    for raw in extra:
        r = RequirementSpec.model_validate(raw)
        if r.id in seen or r.text.strip().lower() in texts:
            continue
        spec.requirements.append(r)
        seen.add(r.id)
    for rule in pack.hard_rules:
        if rule.id not in seen and not any(rule.rule and rule.rule == r.rule for r in spec.requirements):
            spec.requirements.append(rule.model_copy())
            seen.add(rule.id)


def _apply_pack(spec: CallSpec, pack) -> list[str]:
    notes = []
    if not spec.criteria and pack.criteria_hints:
        spec.criteria = [CriterionSpec.model_validate({"text": "", **c}) for c in pack.criteria_hints]
        notes.append("criteria taken from the funder pack (none parsed from the call)")
    if not spec.sections and pack.outline_text():
        spec.sections = outline_to_sections(pack.outline_text())
        notes.append("sections taken from the funder pack outline (none parsed from the call)")
    for s in spec.sections:
        if s.kind == "other" and s.id.split(".")[0] in pack.section_kinds:
            s.kind = pack.section_kinds[s.id.split(".")[0]]  # type: ignore[assignment]
    if spec.abstract_word_limit is None and pack.abstract_word_limit:
        spec.abstract_word_limit = pack.abstract_word_limit
    if spec.total_page_limit is None and pack.total_page_limit:
        spec.total_page_limit = pack.total_page_limit
    for a in pack.annexes:
        if a not in spec.annexes:
            spec.annexes.append(a)
    if not any(s.kind == "abstract" for s in spec.sections):
        spec.sections.insert(0, SectionSpec(id="0", title="Abstract / Summary", kind="abstract",
                                            word_limit=spec.abstract_word_limit, weight=0.0,
                                            guidance="One-page summary written last from the finished sections."))
        notes.append("added an abstract section (the call defines none)")
    return notes


def _outline_markdown(spec: CallSpec) -> str:
    lines = [f"# Proposal outline — {spec.title}", "",
             f"Funder: {spec.funder} | Instrument: {spec.instrument or '-'} | Pack: {spec.pack}", ""]
    if spec.criteria:
        lines += ["## Evaluation criteria", "", "| ID | Criterion | Max | Weight | Threshold |", "|---|---|---|---|---|"]
        for c in spec.criteria:
            lines.append(f"| {c.id} | {c.name} | {c.max_score:g} | {c.weight:g} | {c.threshold if c.threshold is not None else '-'} |")
        lines.append("")
    lines += ["## Sections", ""]
    for s in spec.sections:
        limit = f" ({s.word_limit} words)" if s.word_limit else (f" ({s.page_limit:g} pages)" if s.page_limit else "")
        lines.append(f"## {s.id}. {s.title}{limit}")
        if s.guidance:
            lines.append(f"- {s.guidance}")
        if s.criterion_ids:
            lines.append(f"- Serves criteria: {', '.join(s.criterion_ids)}")
        lines.append("")
    if spec.requirements:
        lines += ["## Requirements", ""]
        for r in spec.requirements:
            lines.append(f"- [{r.kind}{', disqualifying' if r.disqualifying else ''}] {r.id}: {r.text}")
    return "\n".join(lines)


@handler("parse_call.merge")
async def merge(rt: JobRuntime) -> dict[str, Any]:
    parsed = rt.result_of("parse_call")
    spec = CallSpec.model_validate(parsed["callspec"])
    pack = rt.ctx.packs.get(parsed.get("pack") or "generic", rt.ctx.packs["generic"])
    notes = _apply_pack(spec, pack)
    _merge_requirements(spec, rt.result_of("parse_eligibility").get("requirements", []), pack)
    node_id = ingest_callspec(rt.graph, spec, job_id=rt.job.id)
    rt.graph.put_document("outline", "Proposal outline", _outline_markdown(spec), created_by=rt.job.id)
    project = rt.ws.get_project(rt.project_id)
    project.settings["pack"] = pack.id
    project.funder = project.funder or spec.funder
    project.mechanism = project.mechanism or spec.instrument
    project.deadline = project.deadline or spec.deadline
    rt.ws.store.put_project(project)
    rt.ctx.materialize()
    return {"callspec_id": node_id, "notes": notes, "sections": len(spec.sections), "criteria": len(spec.criteria),
            "summary": f"CallSpec {node_id}: {len(spec.sections)} sections, {len(spec.criteria)} criteria" +
                       (f" ({'; '.join(notes)})" if notes else "")}


@handler("parse_call.approve")
async def approve(rt: JobRuntime) -> dict[str, Any]:
    spec = rt.ctx.callspec()
    if spec is None:
        raise JobFailed("no CallSpec to approve")
    rows = [{"id": f"section:{s.id}", "summary": f"{s.id}. {s.title} [{s.kind}]" +
             (f" — {s.word_limit} words" if s.word_limit else "")} for s in spec.sections]
    rows += [{"id": f"criterion:{c.id}", "summary": f"{c.id} {c.name} (max {c.max_score:g}, weight {c.weight:g})"}
             for c in spec.criteria]
    rows += [{"id": f"requirement:{r.id}", "summary": f"[{r.kind}] {r.text[:120]}"}
             for r in spec.requirements if r.disqualifying]
    answer = await rt.approve("Confirm the parsed call", "Check the sections, criteria and disqualifying "
                              "requirements. Reject rows that are wrong; add notes for corrections.", rows,
                              decisions=["approve", "reject"], key="approve_outline")
    decisions = answer.get("rows") or {}
    rejected = [k for k, v in decisions.items() if v == "reject"]
    if answer.get("decision") == "reject" and not rejected:
        rejected = [r["id"] for r in rows]
    if rejected:
        kept_sections = [s for s in spec.sections if f"section:{s.id}" not in rejected]
        kept_criteria = [c for c in spec.criteria if f"criterion:{c.id}" not in rejected]
        for r in spec.requirements:
            if f"requirement:{r.id}" in rejected:
                r.status = "not_applicable"
        spec.sections, spec.criteria = kept_sections, kept_criteria
        ingest_callspec(rt.graph, spec, job_id=rt.job.id)
        rt.graph.put_document("outline", "Proposal outline", _outline_markdown(spec), created_by=rt.job.id)
    rt.log_decision("Approve parsed call structure?", "approved" if not rejected else f"approved with {len(rejected)} rows removed",
                    [answer.get("note", "user approval via inbox")], type="callspec_approved")
    return {"rejected": rejected, "summary": f"approved ({len(rejected)} rows removed)"}


# ------------------------------------------------------------------ scope configuration

def scope_form_schema(scope: ScopeConfig) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for m in MODULES:
        mod = scope.module(m)
        locked = scope.locked(m)
        props[m] = {"type": "string", "title": MODULE_LABEL[m],
                    "enum": ["required"] if locked else list(STATES),
                    "description": mod.reason +
                        (f" (required by the {mod.source}; cannot be changed)" if locked else "")}
        if locked:
            props[m]["readOnly"] = True
    return {"type": "object", "properties": props}


def _read_scope_answer(proposed: ScopeConfig, answer: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    data = answer.get("data") or {}
    chosen, notes = {}, []
    for m in MODULES:
        value = data.get(m)
        if value in STATES:
            chosen[m] = value
        else:
            notes.append(f"{m}: derived value '{proposed.state(m)}' used")
    return chosen, notes


@handler("parse_call.configure_scope")
async def configure_scope(rt: JobRuntime) -> dict[str, Any]:
    ws, pid = rt.ws, rt.project_id
    derived = ws.recommend_scope(pid)
    current = ws.get_scope(pid)
    proposed = rederive(current, derived) if current is not None else derived
    question = ("User preference controls optional work; call requirements control mandatory work. "
                "Choose for each module whether it is excluded, included or required.")
    example = {m: proposed.state(m) for m in MODULES}
    answer = await rt.form(SCOPE_HEADER, question, scope_form_schema(proposed), key="configure_scope", example=example)
    chosen, notes = _read_scope_answer(proposed, answer)
    try:
        scope = apply_scope_change(proposed, chosen, by="researcher", reason="confirmed at intake")
    except ValueError as e:
        answer = await rt.form(SCOPE_HEADER, f"{e}. {question}", scope_form_schema(proposed),
                               key="configure_scope_retry", example=example)
        chosen, more = _read_scope_answer(proposed, answer)
        notes += more
        try:
            scope = apply_scope_change(proposed, chosen, by="researcher", reason="confirmed at intake")
        except ValueError as e2:
            notes.append(f"kept the derived value for invalid choices: {e2}")
            scope = proposed
            for m, s in chosen.items():                       # apply the valid choices, skip the offending ones
                try:
                    scope = apply_scope_change(scope, {m: s}, by="researcher", reason="confirmed at intake")
                except ValueError:
                    continue
            scope = apply_scope_change(scope, {}, by="engine", reason="derived values kept")
    ws.put_scope(pid, scope)
    rt.log_decision("Which optional modules does the proposal include?", scope.summary(),
                    [f"{m}: {scope.module(m).reason}" for m in MODULES] + notes, type="scope_configured")
    rt.emit("scope:configured", scope=scope.model_dump(mode="json"))
    return {"scope": scope.model_dump(mode="json"), "summary": scope.summary()}


# ------------------------------------------------------------------ concept alignment

@handler("parse_call.align_concept")
async def align_concept(rt: JobRuntime) -> dict[str, Any]:
    spec = rt.ctx.callspec()
    if spec is None:
        raise JobFailed("parse the call first")
    ctx_doc = rt.graph.document("context")
    hyp = hypothesis_of(ctx_doc)
    d = rt.project_dir
    inputs = [("research context", str(d / "context.md")),
              ("call spec", str(d / "intermediate" / "call_spec.json")),
              ("proposal outline", str(d / "intermediate" / "proposal_outline.md"))]
    if (d / "intermediate" / "ideation_brief.json").exists():
        inputs.append(("ideation brief", str(d / "intermediate" / "ideation_brief.json")))
    crit_ids = ", ".join(c.id for c in spec.criteria) or "none parsed"
    instructions = f"""CALL ALIGNMENT CHECK — not a framing evaluation. The hypothesis below was developed before the
call was parsed. Assess how well it fits `{spec.title}` ({spec.funder}, {spec.instrument or 'n/a'}).
Hypothesis: {hyp}
Return a `ConceptAlignment`: one `criterion_fits` entry per evaluation criterion (ids: {crit_ids}); `scope_misfits`
for TRL, geography, consortium, duration, budget or topic mismatches; `eligibility_conflicts` for requirements the
idea may violate; `suggested_hypothesis` only when changes would improve the fit (null when it fits as is);
`verdict` fits | fits_with_changes | does_not_fit; `rationale` in 3-8 sentences."""
    res = await rt.agent("idea_evaluator", phase="align", inputs=inputs, instructions=instructions,
                         output_model=ConceptAlignment, allowed_writes=set(),
                         output_contract="Return the final result as a single JSON object conforming to the "
                         "`ConceptAlignment` schema (the runner validates it and persists every node it contains). "
                         "Do not also write the same JSON to a file.")
    al = ConceptAlignment.model_validate(res.structured)
    rt.graph.put_document("concept_alignment", "Concept alignment with the call", al.rationale,
                          created_by=rt.job.id, **al.model_dump(mode="json", exclude={"rationale"}))
    suggested = (al.suggested_hypothesis or "").strip()
    options = ["keep the hypothesis as is"]
    if suggested and suggested != hyp:
        options.append("adopt the suggested hypothesis")
    options.append("reopen ideation")
    lines = [f"Verdict: {al.verdict} (overall fit {al.overall_fit:g}/10).", al.rationale]
    if al.scope_misfits:
        lines.append("Scope misfits: " + "; ".join(al.scope_misfits))
    if al.eligibility_conflicts:
        lines.append("Eligibility conflicts: " + "; ".join(al.eligibility_conflicts))
    if "adopt the suggested hypothesis" in options:
        lines.append(f"Suggested hypothesis: {suggested}")
    ans = await rt.ask("\n\n".join(lines), options, header=ALIGN_HEADER, key="align_decision")
    choice = str(ans.get("choice") or ans.get("text") or "").strip().lower()
    question = "Does the preliminary concept fit the call?"
    if choice.startswith("reopen"):
        rt.log_decision(question, "reopen_ideation", [al.rationale], type="concept_alignment")
        return {"verdict": al.verdict, "decision": "reopen_ideation",
                "summary": "concept sent back to ideation (still preliminary)"}
    if choice.startswith("adopt") and "adopt the suggested hypothesis" in options:
        replace_hypothesis(rt.graph, suggested, suggested, created_by=rt.job.id, concept_status="aligned")
        rt.log_decision(question, "adopted", [f"previous hypothesis: {hyp}", al.rationale], type="concept_alignment")
        rt.ctx.materialize()
        return {"verdict": al.verdict, "decision": "adopted", "summary": "suggested hypothesis adopted; concept aligned"}
    rt.ws.set_concept_status(rt.project_id, "aligned")
    rt.log_decision(question, "kept", [al.rationale], type="concept_alignment")
    return {"verdict": al.verdict, "decision": "kept", "summary": f"concept aligned ({al.verdict})"}
