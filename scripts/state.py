#!/usr/bin/env python3
"""Deterministic state management for ProposalWriter projects.

All state.json edits and memory-store appends should go through this script
so pipeline state stays machine-valid. Slash commands call it instead of
hand-editing files.

Usage:
  state.py init <project> --agency S --mechanism S [--topic S] [--deadline S]
  state.py stage <project> <stage> <status>       # pending|in_progress|complete
  state.py gate <project> <gate> <true|false>
  state.py append <project> <store> (--json 'OBJ' | --stdin)
  state.py show <project>
  state.py projects

All subcommands accept --runs-dir DIR (default: <repo>/runs).
Exit codes: 0 ok, 1 validation/usage error, 2 project not found.
"""

import argparse
import glob
import json
import os
import sys
from datetime import date, datetime, timezone

try:
    import jsonschema
except ImportError:
    jsonschema = None

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STAGES = [
    "ideation", "call_parsing", "research", "writing", "finance", "figures",
    "business_plan", "review", "external_review",
]
GATES = ["scope", "evidence", "draft", "submission", "external_feedback"]
# "skipped" marks optional stages (e.g. ideation) deliberately bypassed;
# current_stage() treats skipped like complete.
STAGE_STATUSES = ("pending", "in_progress", "complete", "skipped")

STORES = {
    "evidence_store": None,  # store lines are single source entries; see below
    "claim_registry": "claim.json",
    "decision_log": "decision.json",
    "task_registry": "task.json",
    "feedback_log": "feedback_entry.json",
}

MEMORY_FILES = ["evidence_store.jsonl", "claim_registry.jsonl",
                "decision_log.jsonl", "task_registry.jsonl"]
PROJECT_DIRS = ["inputs", "intermediate", "drafts", "reviews", "final", "figures",
                "memory"]


def normalize_gate(name):
    return name.replace("-", "_")


def default_runs_dir():
    return os.environ.get("PW_RUNS_DIR") or os.path.join(REPO_ROOT, "runs")


def project_dir(runs, project):
    d = os.path.join(runs, project)
    if not os.path.isdir(d):
        print(f"error: project '{project}' not found under {runs}", file=sys.stderr)
        sys.exit(2)
    return d


def state_path(runs, project):
    return os.path.join(project_dir(runs, project), "state.json")


def load_state(runs, project):
    path = state_path(runs, project)
    if not os.path.exists(path):
        print(f"error: {path} does not exist", file=sys.stderr)
        sys.exit(2)
    with open(path) as f:
        return json.load(f)


def save_state(runs, project, state):
    path = os.path.join(runs, project, "state.json")
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def set_stage(runs, project, stage, status):
    """Set a stage status; auto-adds missing stage keys (legacy projects)."""
    state = load_state(runs, project)
    stages = state.setdefault("stages", {})
    entry = stages.setdefault(stage, {})
    entry["status"] = status
    entry["updated_at"] = date.today().isoformat()
    save_state(runs, project, state)
    return state


def set_gate(runs, project, gate, passed):
    """Set a gate result; auto-adds missing gate keys (legacy projects)."""
    gate = normalize_gate(gate)
    state = load_state(runs, project)
    gates = state.setdefault("gates", {})
    entry = gates.setdefault(gate, {})
    entry["passed"] = passed
    entry["checked_at"] = datetime.now(timezone.utc).isoformat()
    save_state(runs, project, state)
    return state


def load_schema(name):
    path = os.path.join(REPO_ROOT, "schemas", name)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def validate_entry(store, entry):
    """Validate a JSONL entry against its store's schema. Returns error list."""
    schema_name = STORES.get(store)
    if store == "evidence_store":
        # Store lines are single source objects (the `sources` items of
        # evidence_result.json); require the identifying fields.
        errors = []
        for field in ("source_id", "title"):
            if field not in entry:
                errors.append(f"Missing required field: '{field}'")
        return errors
    schema = load_schema(schema_name) if schema_name else None
    if schema is None:
        return []
    if jsonschema is not None:
        return [
            f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
            for e in jsonschema.Draft7Validator(schema).iter_errors(entry)
        ][:10]
    return [f"Missing required field: '{f}'"
            for f in schema.get("required", []) if f not in entry]


def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        return sum(1 for line in f if line.strip())


def read_jsonl(path):
    entries = []
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def feedback_summary(memory_dir):
    """Group feedback_log by feedback_id (last line wins), summarize per round."""
    path = os.path.join(memory_dir, "feedback_log.jsonl")
    if not os.path.exists(path):
        return None
    current = {}
    for entry in read_jsonl(path):
        fid = entry.get("feedback_id")
        if fid:
            current[fid] = entry
    rounds = {}
    for entry in current.values():
        rnd = entry.get("round", 0)
        status = entry.get("status", "unknown")
        rounds.setdefault(rnd, {}).setdefault(status, 0)
        rounds[rnd][status] += 1
    return {str(k): rounds[k] for k in sorted(rounds)}


def current_stage(state):
    stages = state.get("stages", {})
    for stage in STAGES:
        if stages.get(stage, {}).get("status") in ("pending", "in_progress"):
            return stage
    return "done"


# ---------------------------------------------------------------- subcommands

def cmd_init(args):
    runs = args.runs_dir
    target = os.path.join(runs, args.project)
    if os.path.exists(target):
        print(f"error: {target} already exists — refusing to overwrite",
              file=sys.stderr)
        sys.exit(1)
    for sub in PROJECT_DIRS:
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    for mem in MEMORY_FILES:
        open(os.path.join(target, "memory", mem), "a").close()
    state = {
        "project_name": args.project,
        "funding_agency": args.agency,
        "mechanism": args.mechanism,
        "created_at": date.today().isoformat(),
        "stages": {s: {"status": "pending"} for s in STAGES},
        "gates": {g: {"passed": False} for g in GATES},
    }
    save_state(runs, args.project, state)
    context = os.path.join(target, "context.md")
    with open(context, "w") as f:
        f.write(f"# {args.project} — Research Context\n\n")
        f.write(f"**Funding agency**: {args.agency}\n")
        f.write(f"**Mechanism**: {args.mechanism}\n")
        if args.topic:
            f.write(f"**Topic**: {args.topic}\n")
        if args.deadline:
            f.write(f"**Deadline**: {args.deadline}\n")
        f.write("\n## Hypothesis\n\n_To be completed._\n")
    print(json.dumps({"created": target, "stages": STAGES, "gates": GATES}))


def cmd_stage(args):
    if args.status not in STAGE_STATUSES:
        print(f"error: status must be one of {STAGE_STATUSES}", file=sys.stderr)
        sys.exit(1)
    state = set_stage(args.runs_dir, args.project, args.stage, args.status)
    print(json.dumps({"project": args.project,
                      "stage": args.stage,
                      "status": state["stages"][args.stage]["status"]}))


def cmd_gate(args):
    passed = args.passed.lower() in ("true", "1", "yes", "pass", "passed")
    gate = normalize_gate(args.gate)
    state = set_gate(args.runs_dir, args.project, gate, passed)
    print(json.dumps({"project": args.project, "gate": gate,
                      "passed": state["gates"][gate]["passed"]}))


def cmd_append(args):
    if args.store not in STORES:
        print(f"error: store must be one of {sorted(STORES)}", file=sys.stderr)
        sys.exit(1)
    raw = args.json if args.json else sys.stdin.read()
    try:
        entry = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: entry is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    errors = validate_entry(args.store, entry)
    if errors:
        print(f"error: entry does not conform to the {args.store} schema:",
              file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)
    path = os.path.join(project_dir(args.runs_dir, args.project),
                        "memory", f"{args.store}.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(json.dumps({"appended": args.store,
                      "lines": count_lines(path)}))


def cmd_show(args):
    state = load_state(args.runs_dir, args.project)
    pdir = os.path.join(args.runs_dir, args.project)
    memory = os.path.join(pdir, "memory")
    out = {
        "state": state,
        "current_stage": current_stage(state),
        "stores": {
            store: count_lines(os.path.join(memory, f"{store}.jsonl"))
            for store in STORES
        },
        "drafts": sorted(f for f in os.listdir(os.path.join(pdir, "drafts"))
                         if not f.startswith(".")) if os.path.isdir(
                             os.path.join(pdir, "drafts")) else [],
        "reviews": sorted(f for f in os.listdir(os.path.join(pdir, "reviews"))
                          if not f.startswith(".")) if os.path.isdir(
                              os.path.join(pdir, "reviews")) else [],
        "feedback_rounds": feedback_summary(memory),
    }
    print(json.dumps(out, indent=2))


def cmd_projects(args):
    runs = args.runs_dir
    rows = []
    for state_file in glob.glob(os.path.join(runs, "*", "state.json")):
        try:
            with open(state_file) as f:
                state = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        rows.append({
            "project": os.path.basename(os.path.dirname(state_file)),
            "current_stage": current_stage(state),
            "modified": datetime.fromtimestamp(
                os.path.getmtime(state_file), tz=timezone.utc).isoformat(),
        })
    rows.sort(key=lambda r: r["modified"], reverse=True)
    print(json.dumps(rows, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", default=default_runs_dir())
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("project")
    p.add_argument("--agency", required=True)
    p.add_argument("--mechanism", required=True)
    p.add_argument("--topic")
    p.add_argument("--deadline")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("stage")
    p.add_argument("project")
    p.add_argument("stage")
    p.add_argument("status")
    p.set_defaults(func=cmd_stage)

    p = sub.add_parser("gate")
    p.add_argument("project")
    p.add_argument("gate")
    p.add_argument("passed")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("append")
    p.add_argument("project")
    p.add_argument("store")
    p.add_argument("--json")
    p.add_argument("--stdin", action="store_true")
    p.set_defaults(func=cmd_append)

    p = sub.add_parser("show")
    p.add_argument("project")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("projects")
    p.set_defaults(func=cmd_projects)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
