"""ScopeConfig: derivation precedence, change rules, concept status."""
import pytest

from agency.domain.callspec import CallSpec, SectionSpec
from agency.domain.scope import (MODULES, ScopeConfig, apply_scope_change, concept_status_of, derive_scope,
                                 hypothesis_of, rederive)
from agency.funders.packs import FunderPack


def _spec(**kw):
    sections = [SectionSpec(id="1", title="Excellence", kind="excellence")]
    return CallSpec(call_id="C", title="T", funder="F", sections=sections + kw.pop("sections", []),
                    criteria=[], **kw)


def test_derive_defaults_to_excluded_without_a_call():
    s = derive_scope(None)
    assert [s.state(m) for m in MODULES] == ["excluded"] * 4
    assert all(s.module(m).source == "default" for m in MODULES)
    assert s.configured_at is None


def test_call_requirements_win_over_everything():
    spec = _spec(sections=[SectionSpec(id="4", title="Financial", kind="financial")],
                 annexes=["Business Plan"])
    pack = FunderPack(id="p", name="P", modules={"finance": "excluded", "business_plan": "excluded"})
    s = derive_scope(spec, pack, {"finance": "excluded"})
    assert s.finance.state == "required" and s.finance.source == "call"
    assert s.business_plan.state == "required" and s.business_plan.source == "call"
    assert s.locked("finance") and s.locked("business_plan")
    assert s.required() == ["finance", "business_plan"]


def test_pack_then_preference_then_default():
    pack = FunderPack(id="p", name="P", modules={"figures": "required"})
    s = derive_scope(_spec(), pack, {"figures": "excluded", "external_review": "included"})
    assert s.figures.state == "required" and s.figures.source == "pack" and s.locked("figures")
    assert s.external_review.state == "included" and s.external_review.source == "user"
    assert s.finance.state == "excluded" and s.finance.source == "default"


def test_figures_included_when_the_call_mentions_them():
    assert derive_scope(_spec(), call_text="Include a Gantt chart of the work plan").figures.state == "included"
    spec = _spec(sections=[SectionSpec(id="3", title="Plan", guidance="Provide a diagram of the architecture")])
    assert derive_scope(spec).figures.state == "included"
    assert derive_scope(_spec(), call_text="no visuals").figures.state == "excluded"


def test_apply_change_rules():
    s = derive_scope(_spec(sections=[SectionSpec(id="4", title="Fin", kind="financial")]))
    with pytest.raises(ValueError, match="finance is required by the call"):
        apply_scope_change(s, {"finance": "included"})
    with pytest.raises(ValueError, match="unknown module"):
        apply_scope_change(s, {"budget": "included"})
    with pytest.raises(ValueError, match="invalid state"):
        apply_scope_change(s, {"figures": "maybe"})
    s2 = apply_scope_change(s, {"figures": "required", "finance": "required"}, by="cli", reason="want plots")
    assert s2.figures.state == "required" and s2.figures.source == "user" and s2.figures.reason == "want plots"
    assert s2.finance.source == "call"                       # a no-op on a locked module keeps its source
    assert s2.configured_at and not s2.locked("figures")     # user-required is not locked
    s3 = apply_scope_change(s2, {"figures": "excluded"})
    assert s3.figures.state == "excluded"


def test_rederive_keeps_user_choices_and_applies_call_upgrades():
    first = apply_scope_change(derive_scope(_spec()), {"figures": "included", "external_review": "included"})
    stamp = first.configured_at
    # nothing changed in the call → user choices and the confirmation survive
    again = rederive(first, derive_scope(_spec()))
    assert again.figures.state == "included" and again.configured_at == stamp
    # the call now requires finance → upgraded and the confirmation is reset
    spec2 = _spec(sections=[SectionSpec(id="4", title="Fin", kind="financial")])
    up = rederive(first, derive_scope(spec2))
    assert up.finance.state == "required" and up.finance.source == "call"
    assert up.figures.state == "included" and up.configured_at is None
    # the requirement disappears again → falls back to derivation (default excluded), confirmation reset
    down = rederive(up, derive_scope(_spec()))
    assert down.finance.state == "excluded" and down.finance.source == "default" and down.configured_at is None


def test_load_and_save_round_trip():
    class P:  # duck-typed project
        settings: dict = {}
    p = P()
    assert ScopeConfig.load(p) is None
    s = derive_scope(_spec())
    s.save(p)
    assert ScopeConfig.load(p) == s
    p.settings["scope"] = {"garbage": True}
    assert ScopeConfig.load(p) is None
    assert "finance: excluded (default)" in s.summary()


def test_concept_status_helpers():
    class Doc:
        def __init__(self, data):
            self.data = data
    assert concept_status_of(None) == "none"
    assert concept_status_of(Doc({"hypothesis": "_To be completed._"})) == "none"
    assert hypothesis_of(Doc({"hypothesis": "  A digital twin  "})) == "A digital twin"
    assert concept_status_of(Doc({"hypothesis": "A digital twin"})) == "preliminary"
    assert concept_status_of(Doc({"hypothesis": "A digital twin", "concept_status": "aligned"})) == "aligned"


# ---- workspace scope integration tests ----
from agency.domain.graph import NodeType


def test_workspace_scope_round_trip(ws, project):
    assert ws.get_scope("demo") is None
    rec = ws.recommend_scope("demo")                       # no call spec yet → all excluded
    assert rec.finance.state == "excluded" and rec.configured_at is None
    s = ws.set_scope("demo", {"figures": "included"}, by="test", reason="plots wanted")
    assert s.figures.state == "included" and s.configured_at
    assert ws.get_scope("demo").figures.state == "included"
    d = ws.graph("demo").decisions("scope_changed")
    assert len(d) == 1 and "figures: excluded -> included" in d[0].data["decision"]
    assert ws.status("demo")["scope"]["figures"]["state"] == "included"
    # a call that requires finance locks it
    from tests.test_engine import CALLSPEC
    spec = dict(CALLSPEC, sections=CALLSPEC["sections"] + [{"id": "4", "title": "Financial", "kind": "financial"}])
    ws.graph("demo").add(NodeType.CALL_SPEC, spec)
    assert ws.recommend_scope("demo").finance.state == "required"
    ws.put_scope("demo", ws.recommend_scope("demo"))
    with pytest.raises(ValueError):
        ws.set_scope("demo", {"finance": "excluded"})


def test_workspace_concept_status_and_preferences(ws):
    p = ws.create_project("Pref", project_id="pref", scope_preferences={"external_review": "included"})
    assert p.settings["scope_preferences"] == {"external_review": "included"}
    assert ws.concept_status("pref") == "none"
    assert ws.recommend_scope("pref").external_review.state == "included"
    ws.create_project("Hyp", project_id="hyp", hypothesis="A twin cuts scrap")
    assert ws.concept_status("hyp") == "preliminary"
    ws.set_concept_status("hyp", "aligned")
    assert ws.concept_status("hyp") == "aligned"
    with pytest.raises(ValueError):
        ws.set_concept_status("hyp", "maybe")


def test_stage_order_is_call_first(ws):
    from agency.workspace import STAGES
    assert STAGES[:2] == ["call_parsing", "ideation"]
    p = ws.create_project("Blank", project_id="blank")
    assert ws.current_stage(p) == "call_parsing"


def test_replace_hypothesis_sets_status(ws, project):
    from agency.jobs.common import replace_hypothesis
    g = ws.graph("demo")
    replace_hypothesis(g, "New idea\n\n**Mechanism**: x", "New idea", created_by="t", concept_status="aligned")
    doc = g.document("context")
    assert doc.data["hypothesis"] == "New idea" and doc.data["concept_status"] == "aligned"
    assert doc.data["body"].count("## Hypothesis") == 1 and "**Mechanism**: x" in doc.data["body"]
    from agency.domain.models import ConceptAlignment
    al = ConceptAlignment(overall_fit=7, verdict="fits", criterion_fits=[], rationale="ok")
    assert al.suggested_hypothesis is None
