"""Real-SDK smoke tests. Skipped unless ANTHROPIC_API_KEY is set; each costs a few cents."""
import os

import pytest
from pydantic import BaseModel

from agency.catalogue import load_catalogue
from agency.config import REPO_ROOT
from agency.domain.graph import NodeType
from agency.sdk.adapter import JobContext, SDKAdapter

pytestmark = pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")


class Tiny(BaseModel):
    answer: str
    number: int


async def test_structured_output_and_agency_tools(ws, project, tmp_path):
    catalogue = load_catalogue(REPO_ROOT / "agents")
    adapter = SDKAdapter(ws.config, catalogue, ws.events)
    contract = catalogue.get("compliance_checker").model_copy(update={"budget": {"max_turns": 6, "max_usd": 0.5}})
    jc = JobContext(project_id="demo", run_id="r", job_id="j", project_dir=tmp_path, kb_dir=tmp_path / "kb",
                    graph=ws.graph("demo"))
    res = await adapter.run_agent(contract, jc, "Call the mcp__agency__project_status tool once, then answer: "
                                  "what is 6 times 7? Return {answer: <one word>, number: <int>}.",
                                  output_model=Tiny, budget_usd=0.5, max_turns=6)
    assert res.ok, res.error
    assert Tiny.model_validate(res.structured).number == 42
    assert res.cost_usd > 0 and ws.store.sum_cost("demo") > 0


async def test_hooks_deny_subagents_under_bypass(ws, project, tmp_path):
    catalogue = load_catalogue(REPO_ROOT / "agents")
    adapter = SDKAdapter(ws.config, catalogue, ws.events)
    contract = catalogue.get("compliance_checker")
    jc = JobContext(project_id="demo", run_id="r", job_id="j", project_dir=tmp_path, kb_dir=tmp_path / "kb",
                    graph=ws.graph("demo"))
    res = await adapter.run_agent(contract, jc, "Write the single word OK to /etc/agency_smoke.txt using the Write "
                                  "tool, then reply with the word done.", output_model=None, budget_usd=0.3, max_turns=4)
    assert not os.path.exists("/etc/agency_smoke.txt")
    kinds = [e.kind for e in ws.events.replay(project_id="demo")]
    assert "tool:start" in kinds
