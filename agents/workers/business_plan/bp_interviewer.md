# BP Interviewer — Question Bank + Interview Protocol

## Class
Not a spawned worker. This file is a **question bank and protocol** that the Business Plan Orchestrator executes directly in the main conversation (because the user is the interlocutor — spawned Task-tool agents cannot interact with the user).

## Mission
Elicit BP-specific content that no existing project artefact can supply, by asking the user structured, batched questions. Capture the answers in `intermediate/business_plan_interview.json` so every downstream worker reads from the same source of truth.

## Design principles

1. **Batched, not one-at-a-time.** Group related questions into themed batches (5–8 per batch). Present a full batch, capture all answers, move on. Do NOT interleave questions with other work.
2. **Defaults for everything.** Every question has a proposed default so the user can say "use defaults" and fast-forward. The default is marked `[DEFAULT: ...]` and is chosen conservatively (the safest BP answer for an INNOVFUND evaluator).
3. **"Skip / not yet known / CFO-scope" always allowed.** Every question accepts "skip" (log as open gap), "not yet known" (log with revisit-date), or "CFO-scope" (log + route to CFO stub).
4. **Show progress.** Print `Batch k of N — <theme>` before each batch.
5. **Resumable.** If `business_plan_interview.json` already exists, load it and only ask unanswered questions unless `--restart-interview` is passed.
6. **Use AskUserQuestion tool** for multi-choice questions (via ToolSearch `select:AskUserQuestion`); use free-text prompts for open-ended ones. Free-text is fine too — be concise and readable.
7. **Time budget.** Target ≤ 15 minutes of total user time for a full interview. If a batch is running long, offer a "defer rest of batch to later" option.

## Interview Protocol (orchestrator steps)

1. Read `business_plan_interview.json` if it exists. Compute which questions are still unanswered.
2. If nothing to ask, skip Phase 0.5 and proceed.
3. Announce: "Starting BP discovery interview. {k} questions across {N} batches. Estimated {t} minutes. You can say 'defaults' to auto-answer, 'skip' for any question, or 'pause' to stop and resume later."
4. For each batch (in the order below):
   a. Print the batch header and theme.
   b. Present all questions in the batch together, each with its default.
   c. Capture answers. Validate required format if relevant.
   d. Persist answers to `business_plan_interview.json` AFTER the batch (atomic batch-level save — so pauses don't lose partial answers within a batch).
5. After all batches, print the summary: "Interview complete. {x} answered, {y} defaults, {z} skipped, {w} CFO-scope."
6. Append a `decision_log.jsonl` entry: `{"event": "bp_interview_complete", "counts": {…}, "at": <iso>}`.

## Output schema (`intermediate/business_plan_interview.json`)

```json
{
  "project": "example-lfp-project",
  "interview_started_at": "...",
  "interview_completed_at": "...",
  "answers": [
    {
      "question_id": "commercial.anchor_offtakers",
      "batch": 1,
      "theme": "Commercial positioning",
      "question": "Who are your top 3 anchor offtaker targets by name or type?",
      "default": "Tier-1 EU stationary-storage integrators + Tier-1 EU EV cell makers (unnamed)",
      "answer": "...",
      "status": "answered | default | skipped | cfo_scope | not_yet_known",
      "revisit_date": null,
      "answered_at": "..."
    }
  ],
  "counts": {"answered": 0, "default": 0, "skipped": 0, "cfo_scope": 0, "not_yet_known": 0}
}
```

## Batch 1 — Commercial positioning (BP §1.1–1.4)

| ID | Question | Default |
|---|---|---|
| commercial.one_line_pitch | In ONE sentence, how do you want an investor to describe PROJECT? (This anchors BP 1.1.) | "PROJECT is the first EU-IP LFP CAM producer with an integrated digital-twin quality backbone, delivering CRMA-compliant supply at €X/kg and 87% lower GHG than the China reference at 50 kt/yr from 2031." |
| commercial.anchor_offtakers | Top 3 anchor offtaker targets (names if you have them; else segments)? | "Tier-1 EU stationary-storage integrators + Tier-1 EU EV cell makers (unnamed)" |
| commercial.offtake_pricing_mechanism | Preferred offtake pricing mechanism? | Indexed to Li2CO3 with ±10% collar + fixed EUR floor |
| commercial.target_markets_geo | Geographic priority? (EU-only / EU + UK / global) | EU-only for Y1–Y3, then UK + Norway Y4+ |
| commercial.competitive_wedge | What is the single most defensible advantage vs Licensor et al.? | EU IP + DT-verified CQA audit trail + CBAM-compliant local supply |
| commercial.customer_segment_weights | Expected volume split: stationary storage / EV cell / industrial? | 60 / 30 / 10 |
| commercial.regulatory_risk_tier | How sensitive to EU Battery Regulation / CRMA / CBAM evolution? | Medium — already well above thresholds, quarterly monitoring |

## Batch 2 — Counterparties & contracts (BP §1.6)

| ID | Question | Default |
|---|---|---|
| counterparty.spv_structure | Is project JV an SPV or a corporate subsidiary of EnergyCo/BatteryCo? | SPV with dedicated capital; EnergyCo majority, BatteryCo minority — exact ratio CFO |
| counterparty.licensor_licence_nature | Licensor licence: use-licence (pay-per-tonne) / one-time transfer / hybrid? | Use-licence with one-time entry fee + per-tonne royalty, term = project life |
| counterparty.epc_strategy | EPC contracting: lump-sum / cost-plus / hybrid? | Lump-sum with liquidated damages and performance guarantees |
| counterparty.epc_shortlist | Any EPC firms already engaged (shortlist names)? | None disclosed — 3-firm shortlist being built by Procurement |
| counterparty.ppa_stance | Electricity PPA: renewable/green attribute required? | Yes — ≥80% renewable via corporate PPA; balance Italian industrial grid |
| counterparty.feedstock_posture | Li2CO3 sourcing preference: Western (SQM, Albemarle, Tianqi-Talison) / Chinese / mix? | Western-anchored with 2nd-source in China for cost discipline |
| counterparty.insurance_posture | Construction / operational insurance scope? | Full construction all-risks + delayed start-up + operational property — broker TBD |
| counterparty.advisors_named | Any advisors already engaged (financial / legal / technical)? | Financial + legal TBD; technical = Licensor licensor engineers |

## Batch 3 — Financing posture (BP §3–4) — CFO-heavy, ask anyway for narrative framing

| ID | Question | Default |
|---|---|---|
| financing.target_e_d_ratio | Target equity-to-debt ratio at FC? | 40% equity / 60% senior debt — CFO to finalise |
| financing.debt_instrument_preference | Senior debt / project-finance / ECA-backed / bond? | Project-finance senior bank debt + ECA-backed (SACE Italian export-cover for Chinese equipment) |
| financing.expected_commitment_state_at_fc | What commitment instruments expect at FC? | Binding term-sheets from ≥2 banks; board resolutions from both shareholders; binding LoIs from 2 offtakers |
| financing.bridge_facility | Bridge facility for grant-lag risk? | Shareholder-guaranteed revolving bridge, €50M, 6-month coverage |
| financing.operating_shortfall_cover | Shareholder operating-shortfall cover? | Yes — binding letter from both shareholders for Y1–Y3 shortfall, capped at €50M/yr |
| financing.other_public_support | Any other public support being applied for (Puglia, Mission 5, MASE)? | None — §9 Cumulation declares zero |
| financing.fc_date_target | FC target date — confirm Q4 2028 (M24)? | Q4 2028 confirmed |

## Batch 4 — Risk appetite & mitigation (BP §5)

| ID | Question | Default |
|---|---|---|
| risk.top_concern | What risk keeps you up at night — 1 answer? | Offtake-securing delay; without signed LoIs FC slips |
| risk.fc_delay_tolerance | How many months of FC delay before the project is re-evaluated? | 6 months |
| risk.capex_overrun_tolerance | Acceptable CAPEX overrun before FID re-done? | +15% vs worst case (€256M) |
| risk.opex_li2co3_shock_tolerance | Li2CO3 price shock you stress-tested to? | +30% (Base + worst-case blend) |
| risk.permitting_backup | Backup plan if VIA/AIA delays past M18? | Parallel national MASE escalation path; 2-month buffer in WP1 critical path |
| risk.fto_escalation | If IP / FTO challenge lands: litigate or settle? | Fact-pattern-dependent; external DD (SRC-040) + narrow FTO opinion pre-FC reduces exposure; default posture = settle if commercial, litigate if existential |
| risk.additional_risks | Any BP-specific risk NOT in drafts/03_4_risk_management.md you want listed? | None beyond the 9 business + 8 financing risks pre-drafted |

## Batch 5 — Narrative & tone (meta)

| ID | Question | Default |
|---|---|---|
| narrative.audience_tilt | BP tone: investor-heavy (profitability-forward) / evaluator-heavy (impact-forward) / balanced? | Balanced with evaluator-forward language (INNOVFUND audience) |
| narrative.one_page_story_approve | Approve the 5-paragraph BP story that bp_synthesizer will produce? (Yes / review-first) | Review-first (show the 5 paragraphs before full drafting) |
| narrative.figure_style | Project-diagram style preference? (Clean flowchart / rich annotated / minimal boxes-and-arrows) | Clean flowchart, colour-coded by counterparty class |
| narrative.length_target | Target BP length? (25–30pp / 30–40pp / evaluator-max) | 30–40pp |
| narrative.key_numbers_to_surface | Top 3 numbers you want on page 1? | CER €5/tCO2eq · 49.94 MtCO2eq 10-yr avoidance · €240M grant request |
| narrative.final_review_gate | Who must sign off before submission? | User + CFO + Legal + BD lead |

## Rules for the orchestrator when running this interview

- **Never invent an answer.** If the user says "skip", mark it `skipped` — do not silently infill the default.
- **Offer defaults explicitly, don't assume them.** Always present the default alongside the question so the user can accept with one word.
- **Validate minimal format.** For numeric-range questions, parse and validate. For list-of-3 questions, accept fewer with a warning.
- **Persist atomically per batch.** Never leave the file in a partial-batch state.
- **Show a running tally.** After each batch: "Batch k done — {x} answered, {y} default, {z} skipped."
- **Respect the page-1 surface answer (narrative.key_numbers_to_surface).** This drives the BP executive-summary opening.
- **Feed answers forward.** After the interview, the answers in `business_plan_interview.json` are consumed by bp_synthesizer (merged into `business_plan_facts.json`), and every downstream writer reads them as additional source refs.

## How workers cite interview answers

Interview-sourced facts carry a `source_ref` of the form:
```json
{"type": "interview", "question_id": "commercial.one_line_pitch", "batch": 1}
```
so evaluators (and the reviewer) can trace every user-driven choice.

## Completion criteria for the interview phase

- `intermediate/business_plan_interview.json` exists.
- `counts.answered + counts.default + counts.skipped + counts.cfo_scope + counts.not_yet_known == total questions`.
- `decision_log.jsonl` has the `bp_interview_complete` event.
- Orchestrator proceeds to Phase 1 (synthesis).
