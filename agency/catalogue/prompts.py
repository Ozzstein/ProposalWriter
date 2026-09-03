"""Prompt composition: conventions + role prompt (system) and the task envelope (user)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .loader import AgentContract, Catalogue

_LEGACY_SUBS = [
    (re.compile(r"runs/\{project(?:-name)?\}"), "{project_dir}"),
    (re.compile(r"(?<![\w/.])wiki/"), "{kb_dir}/"),
    (re.compile(r"`?python3? scripts/state\.py append[^`\n]*`?"), "the `mcp__agency__graph_write` tool"),
    (re.compile(r"`?python3? scripts/state\.py[^`\n]*`?"), "the agency tools"),
    (re.compile(r"scripts/gate_check\.py"), "the gate policy"),
    (re.compile(r"`?\.claude/agents/[^`\s]*`?"), "the agent catalogue"),
    (re.compile(r"schemas/(\w+)\.json"), r"schema `\1`"),
]


def normalise_prompt(text: str) -> str:
    """Rewrite legacy path conventions into placeholders the renderer fills in."""
    for pattern, repl in _LEGACY_SUBS:
        text = pattern.sub(repl, text)
    return text


def fill(text: str, **values: str) -> str:
    for k, v in values.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def system_prompt(catalogue: Catalogue, contract: AgentContract, project_dir: Path | str,
                  kb_dir: Path | str) -> str:
    body = normalise_prompt(contract.load_prompt())
    conv = catalogue.conventions
    return fill(conv + "\n\n---\n\n" + body, project_dir=str(project_dir), kb_dir=str(kb_dir))


@dataclass
class TaskSpec:
    project_id: str
    project_dir: Path
    kb_dir: Path
    run_id: str
    job_id: str
    stage: str
    phase: str = ""
    dedupe_key: str = ""
    inputs: list[tuple[str, str]] = field(default_factory=list)      # (label, path-or-description)
    output_contract: str = ""
    id_ranges: dict[str, tuple[int, int]] = field(default_factory=dict)  # prefix -> (start, end)
    instructions: str = ""
    kb_context: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


def render_task(contract: AgentContract, spec: TaskSpec) -> str:
    lines = [f"# Task for `{contract.name}` — project `{spec.project_id}`", "",
             f"project: {spec.project_id}",
             f"dedupe_key: {spec.dedupe_key or spec.job_id}",
             f"run_id: {spec.run_id} | job_id: {spec.job_id} | stage: {spec.stage}"
             + (f" | phase: {spec.phase}" if spec.phase else ""), "",
             "## Resolved paths (absolute)",
             f"- project_dir: {spec.project_dir}",
             f"- kb_dir: {spec.kb_dir} ({'exists' if Path(spec.kb_dir).exists() else 'not initialised — skip all knowledge-base steps'})",
             ""]
    if spec.inputs:
        lines.append("## Inputs")
        for label, path in spec.inputs:
            p = Path(path)
            status = ""
            if p.is_absolute() or str(path).startswith(str(spec.project_dir)):
                if p.exists():
                    status = f" — {p.stat().st_size} bytes" if p.is_file() else " — directory"
                else:
                    status = " — MISSING"
            lines.append(f"- {label}: {path}{status}")
        lines.append("")
    lines += ["## Output contract", spec.output_contract or _default_output_contract(contract), ""]
    if spec.id_ranges:
        lines.append("## Reserved identifiers")
        for prefix, (a, b) in spec.id_ranges.items():
            lines.append(f"- {prefix}: {prefix}-{a:03d} .. {prefix}-{b:03d} (use in order; do not exceed)")
        lines.append("")
    lines.append("## Constraints")
    for c in ["Do not spawn agents. Do not write outside project_dir.",
              "Never write to memory/*.jsonl or state files directly — use mcp__agency__graph_write.",
              *spec.constraints]:
        lines.append(f"- {c}")
    if spec.tools:
        lines.append(f"- Tools available: {', '.join(spec.tools)}")
    lines.append("")
    if spec.instructions:
        lines += ["## Stage-specific instructions", spec.instructions.strip(), ""]
    if spec.kb_context:
        lines += ["## Knowledge-base context", *[f"- {k}" for k in spec.kb_context], ""]
    for k, v in spec.extra.items():
        lines += [f"## {k}", str(v).strip(), ""]
    return "\n".join(lines).rstrip() + "\n"


def _default_output_contract(contract: AgentContract) -> str:
    if contract.output_mode == "structured":
        return (f"Return the final result as a single JSON object conforming to the `{contract.output}` "
                "schema (the runner validates it and persists every node it contains). Do not also write "
                "the same JSON to a file.")
    if contract.output_mode == "files":
        return ("Write your deliverables as files under project_dir exactly where your role definition "
                "says. The runner validates and ingests them; finish with a short summary listing every "
                "file you wrote.")
    return "This is an interactive session; finish by calling the `mcp__agency__submit_result` tool."
