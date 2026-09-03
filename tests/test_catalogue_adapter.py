import json
from pathlib import Path

import pytest

from agency.catalogue import load_catalogue
from agency.catalogue.prompts import TaskSpec, render_task, system_prompt
from agency.config import REPO_ROOT
from agency.domain.graph import NodeType
from agency.domain.models import Claim, NoveltyMap, Source
from agency.hooks.guards import HookContext, build_hooks
from agency.sdk.adapter import JobContext, SDKAdapter
from agency.tools.server import ToolContext, build_agency_server
from tests.fake_sdk import FakeQuery, make_result

AGENTS_DIR = REPO_ROOT / "agents"


@pytest.fixture(scope="module")
def catalogue():
    return load_catalogue(AGENTS_DIR)


def test_catalogue_is_complete_and_valid(catalogue):
    assert len(catalogue.contracts) == 32
    assert catalogue.validate() == []
    roles = {c.role for c in catalogue.contracts.values()}
    assert {"retriever", "synthesizer", "writer", "reviewer", "interviewer", "renderer", "modeler", "planner"} <= roles
    assert catalogue.get("novelty_mapper").output_model() is NoveltyMap
    assert catalogue.get("excellence_writer").output_mode == "files"
    assert catalogue.get("idea_interviewer").session


BANNED_PROMPT_PATTERNS = [
    # legacy runtime mechanics
    r"/tmp/pw_venv", r"homebrew", r"/opt/", r"firecrawl (search|scrape|map|crawl) ", r"\.firecrawl/",
    r"runs/\{project", r"(?<!figures/)scripts/", r"state\.py", r"gate_check", r"schemas/", r"templates/",
    r"\.claude", r"subagent", r"Program Director", r"(?<!needs_)orchestrator", r"combine_to_docx", r"\.env\b",
    r"evaluation_matrix", r"call_brief", r"wiki/",
    # connectors that no longer exist
    r"Consensus", r"Semantic Scholar",
    # hard-coded identifiers from a previous project (illustrative SRC-012 / CLM-007 are allowed)
    r"(SRC|CLM)-0(?!12\b|07\b)\d\d", r"CLM-FIN", r"WIKI-CLM-xxx",
    # project-specific names and numbers
    r"EnergyCo", r"BatteryCo", r"TwinHeat", r"\bSERI\b", r"Tpl_", r"ROADBLOCKERS", r"example-lfp",
    r"\bLFP\b", r"Puglia", r"Licensor", r"Li2CO3", r"INNOVFUND", r"49\.94", r"€240M",
]


@pytest.mark.parametrize("prompt_path", sorted(AGENTS_DIR.glob("*/prompt.md")), ids=lambda p: p.parent.name)
def test_prompt_hygiene(prompt_path):
    """Role prompts carry only domain rules: no legacy paths, tools, orchestration or project facts."""
    import re
    text = prompt_path.read_text()
    hits = [(pat, m.group(0)) for pat in BANNED_PROMPT_PATTERNS for m in [re.search(pat, text)] if m]
    assert not hits, f"{prompt_path.parent.name}: {hits}"


def test_prompts_render_with_paths(catalogue):
    for c in catalogue.contracts.values():
        sp = system_prompt(catalogue, c, "/ws/p", "/ws/kb")
        assert "/ws/p" in sp and "{project_dir}" not in sp and "{kb_dir}" not in sp, c.name
        assert "runs/{project}" not in sp and "wiki/" not in sp, c.name


def test_task_rendering(catalogue, tmp_path):
    c = catalogue.get("literature_searcher")
    spec = TaskSpec(project_id="demo", project_dir=tmp_path, kb_dir=tmp_path / "kb", run_id="r1", job_id="j1",
                    stage="research", phase="retrieve", inputs=[("context", str(tmp_path / "context.md"))],
                    id_ranges={"SRC": (41, 80)}, instructions="Focus on LFP cathodes.")
    text = render_task(c, spec)
    assert "project: demo" in text and "dedupe_key: j1" in text
    assert "SRC-041 .. SRC-080" in text and "MISSING" in text and "Focus on LFP" in text
    assert "EvidenceResult" in text


async def test_guard_hooks(tmp_path, ws, project):
    ctx = HookContext(project_id="demo", job_id="j1", run_id="r1", agent="x", allowed_roots=[tmp_path],
                      events=ws.events, known_claim_ids={"CLM-001"})
    hooks = build_hooks(ctx)
    guard = hooks["PreToolUse"][0].hooks[0]
    deny = await guard({"tool_name": "Agent", "tool_input": {}}, "t1", None)
    assert deny["hookSpecificOutput"]["permissionDecision"] == "deny"
    deny = await guard({"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "memory/claim_registry.jsonl")}}, "t2", None)
    assert "graph_write" in deny["hookSpecificOutput"]["permissionDecisionReason"]
    deny = await guard({"tool_name": "Write", "tool_input": {"file_path": "/etc/passwd"}}, "t3", None)
    assert deny["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert await guard({"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "drafts/x.md")}}, "t4", None) == {}
    assert "deny" in json.dumps(await guard({"tool_name": "Bash", "tool_input": {"command": "rm -rf / "}}, "t5", None))
    # post-write validation feeds errors back as context
    validate = hooks["PostToolUse"][0].hooks[0]
    bad = tmp_path / "intermediate" / "novelty_map.json"
    bad.parent.mkdir()
    bad.write_text(json.dumps({"project_name": "x"}))
    out = await validate({"tool_name": "Write", "tool_input": {"file_path": str(bad)}}, "t6", None)
    assert "NoveltyMap" in out["hookSpecificOutput"]["additionalContext"]
    draft = tmp_path / "drafts" / "01_x.md"
    draft.parent.mkdir()
    draft.write_text("see CLM-001 and CLM-042")
    out = await validate({"tool_name": "Write", "tool_input": {"file_path": str(draft)}}, "t7", None)
    assert "CLM-042" in out["hookSpecificOutput"]["additionalContext"]
    # telemetry writes events
    await hooks["PreToolUse"][1].hooks[0]({"tool_name": "Read", "tool_input": {"file_path": "a"}}, "t8", None)
    await hooks["PostToolUse"][1].hooks[0]({"tool_name": "Read", "tool_response": "x" * 1000}, "t8", None)
    kinds = [e.kind for e in ws.events.replay(project_id="demo")]
    assert kinds[-2:] == ["tool:start", "tool:end"]


async def test_agency_tools(ws, project):
    g = ws.graph("demo")
    src = g.add(NodeType.SOURCE, Source(title="Paper", extract="x"))
    ctx = ToolContext(graph=g, project_id="demo", job_id="j1", allowed_writes={"Claim"}, events=ws.events)
    server = build_agency_server(ctx)
    assert server["type"] == "sdk" and server["name"] == "agency"
    handlers = ctx.handlers
    out = json.loads((await handlers["graph_read"]({"type": "Source"}))["content"][0]["text"])
    assert out[0]["id"] == src.id
    res = await handlers["graph_write"]({"type": "Claim", "data": {"text": "c", "type": "scientific_finding",
                                                                    "status": "supported", "supported_by": [src.id]}})
    assert json.loads(res["content"][0]["text"])["id"] == "CLM-001"
    res = await handlers["graph_write"]({"type": "Source", "data": {"title": "nope"}})
    assert res.get("is_error")
    res = await handlers["graph_write"]({"type": "Claim", "data": {"text": "c"}})
    assert "validation failed" in res["content"][0]["text"]
    ids = json.loads((await handlers["next_ids"]({"prefix": "SRC", "n": 2}))["content"][0]["text"])
    assert ids == ["SRC-002", "SRC-003"]
    assert "ask_user" not in handlers



async def test_adapter_runs_structured_query(ws, project, catalogue, tmp_path):
    payload = {"project_name": "demo", "minimum_anchors_met": True, "novelty_anchors": [
        {"anchor_id": "NOV-001", "claim": "a", "novelty_type": "first", "dimension": "technical",
         "supported_by": ["SRC-001"], "confidence": "high", "attack_surface": "x", "defensibility_score": 8}]}
    fake = FakeQuery(lambda prompt, options: {"structured": payload, "tool_uses": ["Read"]})
    adapter = SDKAdapter(ws.config, catalogue, ws.events, query_fn=fake)
    jc = JobContext(project_id="demo", run_id="r1", job_id="j1", project_dir=tmp_path, kb_dir=tmp_path / "kb",
                    graph=ws.graph("demo"))
    res = await adapter.run_agent(catalogue.get("novelty_mapper"), jc, "do it")
    assert res.ok and res.structured == payload and res.tool_uses == 1 and res.cost_usd == 0.01
    opts = fake.calls[0]["options"]
    assert opts.model == ws.config.models["reasoning"] and opts.permission_mode == "bypassPermissions"
    assert "Agent" in opts.disallowed_tools and opts.setting_sources == []
    assert "mcp__agency__graph_read" in opts.allowed_tools and "mcp__agency__graph_write" not in opts.allowed_tools
    assert opts.output_format["schema"]["title"] == "NoveltyMap"
    assert "agency" in opts.mcp_servers and opts.env["CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"] == "1"
    assert ws.store.sum_cost("demo") == 0.01
    kinds = [e.kind for e in ws.events.replay(project_id="demo")]
    assert "agent:start" in kinds and kinds[-1] == "agent:end"


async def test_adapter_reports_validation_failure_and_errors(ws, project, catalogue, tmp_path):
    fake = FakeQuery(lambda p, o: {"structured": {"project_name": "demo"}})
    adapter = SDKAdapter(ws.config, catalogue, ws.events, query_fn=fake)
    jc = JobContext(project_id="demo", run_id="r1", job_id="j1", project_dir=tmp_path, kb_dir=tmp_path, graph=ws.graph("demo"))
    res = await adapter.run_agent(catalogue.get("novelty_mapper"), jc, "x")
    assert not res.ok and "validation" in res.error
    fake = FakeQuery(lambda p, o: make_result(None, subtype="error_max_budget_usd", is_error=True, errors=["budget"]))
    adapter = SDKAdapter(ws.config, catalogue, ws.events, query_fn=fake)
    res = await adapter.run_agent(catalogue.get("novelty_mapper"), jc, "x")
    assert not res.ok and res.subtype == "error_max_budget_usd"
    # files-mode contracts succeed on a plain success result
    fake = FakeQuery(lambda p, o: {"structured": None})
    adapter = SDKAdapter(ws.config, catalogue, ws.events, query_fn=fake)
    res = await adapter.run_agent(catalogue.get("excellence_writer"), jc, "x")
    assert res.ok and fake.calls[0]["options"].output_format is None
    assert "Write" in fake.calls[0]["options"].allowed_tools
