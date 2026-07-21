#!/usr/bin/env python3
"""Deterministic review-gate checks for ProposalWriter.

Computes pass/fail for the pipeline gates from project files alone — no
LLM judgment involved. The /gate-check slash command runs this script and
interprets the result.

Usage:
  gate_check.py <project> <gate> [--runs-dir DIR] [--no-write]

Gates: scope | evidence | draft | submission | external-feedback

Output: full gate_check JSON (schemas/gate_check.json) on stdout.
Unless --no-write: also written to
runs/<project>/intermediate/gate_check_<gate>.json, and
state.json gates.<gate>.passed is updated via scripts/state.py.

Exit codes: 0 passed, 1 failed, 2 usage/project error,
            3 not applicable (external-feedback with no feedback log).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state as state_mod  # noqa: E402

GATES = ["scope", "evidence", "draft", "submission", "external-feedback"]

# Thresholds (reconciled with agents/orchestrators/research_orchestrator.md)
MIN_EVIDENCE = 12
MIN_ANCHORS = 3
MIN_GAPS = 4
MAX_UNSUPPORTED_RATIO = 0.20
MAX_ASSUMPTIONS_PER_DRAFT = 2
MIN_SCIENTIFIC_SCORE = 6.0
DEFAULT_ABSTRACT_WORDS = 500

CLAIM_REF_RE = re.compile(r"\b(?:WIKI-)?CLM(?:-FIN)?-\d+\b")
CLOSED_FEEDBACK_STATUSES = {"resolved", "deferred", "rejected", "ack",
                            "stale", "skipped", "unlocatable"}


def crit(name, met, notes=""):
    c = {"criterion": name, "met": bool(met)}
    if notes:
        c["notes"] = notes
    return c


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def nonempty_file(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


# ------------------------------------------------------------------ gates

def check_scope(p):
    criteria = []
    for fname, label in [("call_brief.json", "Call document parsed"),
                         ("evaluation_matrix.json", "Evaluation criteria mapped")]:
        path = os.path.join(p, "intermediate", fname)
        data = load_json(path)
        criteria.append(crit(label, data is not None,
                             f"intermediate/{fname} "
                             + ("parses as JSON" if data is not None
                                else "missing or invalid JSON")))
    outline = os.path.join(p, "intermediate", "proposal_outline.md")
    criteria.append(crit("Proposal outline created", nonempty_file(outline),
                         "intermediate/proposal_outline.md"))
    ctx_path = os.path.join(p, "context.md")
    has_hypothesis = False
    if os.path.exists(ctx_path):
        with open(ctx_path) as f:
            has_hypothesis = bool(re.search(r"hypothes|central idea", f.read(), re.I))
    criteria.append(crit("Research context documented", has_hypothesis,
                         "context.md exists and mentions a hypothesis/central idea"))
    return criteria


def check_evidence(p):
    criteria = []
    entries = state_mod.read_jsonl(os.path.join(p, "memory", "evidence_store.jsonl"))
    source_ids = {e.get("source_id") for e in entries if e.get("source_id")}
    n_sources = len(source_ids) if source_ids else len(entries)
    criteria.append(crit(f"Evidence store has >= {MIN_EVIDENCE} sources",
                         n_sources >= MIN_EVIDENCE, f"{n_sources} unique sources"))
    criteria.append(crit("SOTA summary exists",
                         nonempty_file(os.path.join(p, "intermediate", "sota_summary.md")),
                         "intermediate/sota_summary.md"))
    nov = load_json(os.path.join(p, "intermediate", "novelty_map.json"))
    anchors = len(nov.get("novelty_anchors", [])) if nov else 0
    criteria.append(crit(f"Novelty map has >= {MIN_ANCHORS} anchors",
                         nov is not None and anchors >= MIN_ANCHORS
                         and nov.get("minimum_anchors_met", True),
                         f"{anchors} anchors" if nov else "novelty_map.json missing"))
    gaps = load_json(os.path.join(p, "intermediate", "gap_analysis.json"))
    n_gaps = len(gaps.get("gaps", [])) if gaps else 0
    criteria.append(crit(f"Gap analysis has >= {MIN_GAPS} gaps with top gaps selected",
                         gaps is not None and n_gaps >= MIN_GAPS
                         and bool(gaps.get("top_gaps_for_proposal")),
                         f"{n_gaps} gaps" if gaps else "gap_analysis.json missing"))
    claims = current_claims(p)
    criteria.append(crit("Claim registry populated", len(claims) >= 1,
                         f"{len(claims)} claims"))
    unsupported = [c for c in claims.values() if c.get("status") == "unsupported"]
    ratio = len(unsupported) / len(claims) if claims else 1.0
    criteria.append(crit(f"<= {int(MAX_UNSUPPORTED_RATIO*100)}% unsupported claims",
                         bool(claims) and ratio <= MAX_UNSUPPORTED_RATIO,
                         f"{len(unsupported)}/{len(claims)} unsupported "
                         f"({ratio:.0%})" if claims else "no claims registered"))
    return criteria


def current_claims(p):
    """Claim registry grouped by claim_id, last line wins (append-only)."""
    claims = {}
    for entry in state_mod.read_jsonl(os.path.join(p, "memory", "claim_registry.jsonl")):
        cid = entry.get("claim_id")
        if cid:
            claims[cid] = entry
    return claims


def draft_files(p):
    ddir = os.path.join(p, "drafts")
    if not os.path.isdir(ddir):
        return []
    return sorted(f for f in os.listdir(ddir)
                  if f.endswith(".md") and not f.startswith("."))


def outline_sections(p):
    """Parse numbered top-level sections from proposal_outline.md."""
    path = os.path.join(p, "intermediate", "proposal_outline.md")
    if not os.path.exists(path):
        return []
    sections = []
    with open(path) as f:
        for line in f:
            m = re.match(r"^#{1,3}\s+(?:Section\s+)?(\d+)", line.strip(), re.I)
            if m:
                sections.append(int(m.group(1)))
    return sorted(set(sections))


def check_draft(p):
    criteria = []
    drafts = draft_files(p)
    sections = outline_sections(p)
    if sections:
        missing = []
        for n in sections:
            prefix = f"{n:02d}"
            if not any(d.startswith(prefix) or d.startswith(str(n)) for d in drafts):
                missing.append(n)
        criteria.append(crit("All outline sections have drafts", not missing,
                             f"missing sections: {missing}" if missing
                             else f"{len(sections)} sections covered"))
    else:
        criteria.append(crit("All outline sections have drafts", len(drafts) >= 3,
                             f"outline not machine-parseable — fallback check: "
                             f"{len(drafts)} draft files (need >= 3)"))
    unlinked, over_assumed = [], []
    for d in drafts:
        with open(os.path.join(p, "drafts", d)) as f:
            content = f.read()
        if not CLAIM_REF_RE.search(content):
            unlinked.append(d)
        if content.count("[ASSUMPTION]") > MAX_ASSUMPTIONS_PER_DRAFT:
            over_assumed.append(d)
    criteria.append(crit("All drafts reference claim IDs", drafts and not unlinked,
                         f"no CLM references in: {unlinked}" if unlinked
                         else f"{len(drafts)} drafts checked"))
    criteria.append(crit(f"<= {MAX_ASSUMPTIONS_PER_DRAFT} [ASSUMPTION] markers per draft",
                         not over_assumed,
                         f"over limit: {over_assumed}" if over_assumed else ""))
    abstract = [d for d in drafts if "abstract" in d.lower()]
    limit = abstract_word_limit(p)
    ok, notes = False, "no drafts/*abstract*.md found"
    if abstract:
        with open(os.path.join(p, "drafts", abstract[0])) as f:
            words = len(f.read().split())
        ok = words <= limit
        notes = f"{abstract[0]}: {words} words (limit {limit})"
    criteria.append(crit("Abstract exists and is within word limit", ok, notes))
    return criteria


def abstract_word_limit(p):
    brief = load_json(os.path.join(p, "intermediate", "call_brief.json")) or {}
    for key in ("abstract_word_limit", "summary_word_limit", "summary_limit"):
        if isinstance(brief.get(key), int):
            return brief[key]
    return DEFAULT_ABSTRACT_WORDS


def review_reports(p):
    """Yield (filename, report) for every report object in reviews/*.json.

    A file may hold a single report, a list of reports, or
    {"sections": [...]} — normalize all three.
    """
    rdir = os.path.join(p, "reviews")
    if not os.path.isdir(rdir):
        return
    for fname in sorted(os.listdir(rdir)):
        if not fname.endswith(".json"):
            continue
        data = load_json(os.path.join(rdir, fname))
        if data is None:
            continue
        if isinstance(data, list):
            reports = data
        elif isinstance(data, dict) and isinstance(data.get("sections"), list):
            reports = data["sections"]
        else:
            reports = [data]
        for r in reports:
            if isinstance(r, dict):
                yield fname, r


def check_submission(p):
    criteria = []
    scientific = [(f, r) for f, r in review_reports(p)
                  if r.get("reviewer_type") == "scientific"
                  or f.startswith("scientific_review")]
    low = [(f, r.get("section_name", "?"), r.get("overall_score"))
           for f, r in scientific
           if not isinstance(r.get("overall_score"), (int, float))
           or r["overall_score"] < MIN_SCIENTIFIC_SCORE]
    criteria.append(crit(f"Scientific review score >= {MIN_SCIENTIFIC_SCORE} for all sections",
                         scientific and not low,
                         f"below threshold: {low}" if low else
                         (f"{len(scientific)} section reports pass" if scientific
                          else "no scientific review found")))
    critical = [(f, fx.get("action", "")[:60]) for f, r in review_reports(p)
                for fx in r.get("fixes", [])
                if fx.get("priority") == "critical"]
    criteria.append(crit("No critical issues in review reports", not critical,
                         f"critical fixes open: {critical}" if critical else ""))
    compliance = [(f, r) for f, r in review_reports(p)
                  if r.get("reviewer_type") == "compliance"
                  or f.startswith("compliance_review")]
    unmet = [(f, r.get("major_issues")) for f, r in compliance if r.get("major_issues")]
    criteria.append(crit("Compliance review passes", compliance and not unmet,
                         f"major issues: {unmet}" if unmet else
                         ("pass" if compliance else "no compliance review found")))
    claims = current_claims(p)
    approved = approved_unsupported(p)
    unsupported = [cid for cid, c in claims.items()
                   if c.get("status") == "unsupported" and cid not in approved]
    criteria.append(crit("All unsupported claims resolved or user-approved",
                         not unsupported,
                         f"unresolved: {sorted(unsupported)}" if unsupported else ""))
    return criteria


def approved_unsupported(p):
    """Claim IDs approved via decision_log entries of type approve_unsupported_claim."""
    approved = set()
    for entry in state_mod.read_jsonl(os.path.join(p, "memory", "decision_log.jsonl")):
        if entry.get("type") == "approve_unsupported_claim":
            text = json.dumps(entry)
            approved.update(CLAIM_REF_RE.findall(text))
    return approved


def check_external_feedback(p):
    path = os.path.join(p, "memory", "feedback_log.jsonl")
    if not os.path.exists(path):
        return None  # not applicable
    current = {}
    for entry in state_mod.read_jsonl(path):
        fid = entry.get("feedback_id")
        if fid:
            current[fid] = entry
    criteria = []
    active_round = max((e.get("round", 0) for e in current.values()), default=0)
    open_ids = sorted(fid for fid, e in current.items()
                      if e.get("round", 0) == active_round
                      and e.get("status") in ("open", "in_progress"))
    criteria.append(crit(f"No open/in-progress comments in active round {active_round}",
                         not open_ids,
                         f"still open: {open_ids}" if open_ids else
                         f"{len(current)} comments tracked"))
    bad = sorted(fid for fid, e in current.items()
                 if e.get("status") not in CLOSED_FEEDBACK_STATUSES
                 and e.get("status") not in ("open", "in_progress"))
    criteria.append(crit("All comments have a recognized closed status", not bad,
                         f"unexpected status on: {bad}" if bad else ""))
    stale_unexplained = sorted(fid for fid, e in current.items()
                               if e.get("status") == "stale"
                               and not e.get("resolution"))
    criteria.append(crit("All stale comments have an explanatory resolution",
                         not stale_unexplained,
                         f"missing resolution: {stale_unexplained}"
                         if stale_unexplained else ""))
    return criteria


# ------------------------------------------------------------------ main

CHECKS = {
    "scope": check_scope,
    "evidence": check_evidence,
    "draft": check_draft,
    "submission": check_submission,
    "external-feedback": check_external_feedback,
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("gate", choices=GATES + ["external_feedback"])
    parser.add_argument("--runs-dir", default=state_mod.default_runs_dir())
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    gate = "external-feedback" if args.gate == "external_feedback" else args.gate
    pdir = os.path.join(args.runs_dir, args.project)
    if not os.path.isdir(pdir):
        print(f"error: project '{args.project}' not found under {args.runs_dir}",
              file=sys.stderr)
        sys.exit(2)

    criteria = CHECKS[gate](pdir)

    if criteria is None:  # external-feedback, no log
        result = {
            "gate_name": gate, "passed": False, "not_applicable": True,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "criteria": [],
            "blockers": [],
            "recommendations": ["No external review has been ingested — "
                                "run /external-review first if one is expected."],
        }
        print(json.dumps(result, indent=2))
        sys.exit(3)

    passed = all(c["met"] for c in criteria)
    blockers = [f"{c['criterion']}" + (f" — {c['notes']}" if c.get("notes") else "")
                for c in criteria if not c["met"]]
    result = {
        "gate_name": gate,
        "passed": passed,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "criteria": criteria,
        "blockers": blockers,
        "recommendations": [],
    }

    if not args.no_write:
        out_dir = os.path.join(pdir, "intermediate")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"gate_check_{gate.replace('-', '_')}.json")
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
        state_mod.set_gate(args.runs_dir, args.project, gate, passed)

    print(json.dumps(result, indent=2))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
