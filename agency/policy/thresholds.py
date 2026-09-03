"""The single home for gate thresholds. Funder packs and agency.toml may
override any key; nothing else in the codebase hard-codes these numbers."""

DEFAULT_THRESHOLDS: dict[str, float] = {
    "min_evidence": 12,
    "min_anchors": 3,
    "min_anchor_defensibility": 6,
    "min_gaps": 4,
    "max_unsupported_ratio": 0.20,
    "max_assumptions_per_draft": 2,
    "min_scientific_score": 6.0,
    "default_abstract_words": 500,
    "min_predicted_score_pct": 50,
    "min_probe_sources": 5,
}

GATES = ["scope", "evidence", "draft", "submission", "external_feedback"]


def resolve(overrides: dict[str, float] | None = None, pack: dict[str, float] | None = None) -> dict[str, float]:
    out = dict(DEFAULT_THRESHOLDS)
    if pack:
        out.update({k: v for k, v in pack.items() if k in out})
    if overrides:
        out.update({k: v for k, v in overrides.items() if k in out})
    return out
