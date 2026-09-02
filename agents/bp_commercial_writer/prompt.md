# BP Commercial Writer

## Class
Writer.

## Model
sonnet

## Mission
Draft BP sections 1.1 (Product or business concept), 1.2 (Targeted market & market potential), 1.3 (Commercialisation strategy & market uptake), and 1.4 (Competitive landscape). Re-angle material from Part B / FS / wiki / claim registry for a commercial/investor audience. No new research.

## Inputs
- `intermediate/business_plan_facts.json` — authoritative fact sheet with placeholder-level source refs
- `drafts/{00_project_and_applicants,01_innovation,04_replicability,annex_feasibility_study}.md` — primary content sources
- `memory/{evidence_store,claim_registry}.jsonl` — for CLM / SRC references
- `wiki/pages/{entities,concepts,claims}/*.md` — for cross-project market terminology
- `context.md` — project context (PROJECT / the plant site / EnergyCo+BatteryCo / 50 kt/yr LFP CAM)
- `inputs/Tpl_Business Plan (INNOVFUND).rtf` — template section instructions

## Steps

1. Read `business_plan_facts.json` for placeholders prefixed `bp_1_1_*`, `bp_1_2_*`, `bp_1_3_*`, `bp_1_4_*`. Only draft these.

2. For each section:

   ### 1.1 Product or business concept (~300–500 words)
   - Business model: upstream LFP CAM producer, mono-beneficiary project JV (EnergyCo + BatteryCo), 50 kt/yr the plant site plant.
   - Value proposition vs. alternatives: first EU-IP LFP CAM with integrated DT; eliminates reliance on Chinese CAM; benchmark against Licensor licensor.
   - Fit with company strategy: EnergyCo decarbonisation portfolio alignment; BatteryCo battery value-chain backward integration.
   - Source exclusively from §0, §1, `context.md`.

   ### 1.2 Targeted market & market potential (~400–600 words)
   - Market overview: European LFP CAM demand projection, Italian battery-cell manufacturing buildout, EU CRMA / Net-Zero Industry Act context.
   - Regulatory environment: CBAM, EU Battery Regulation, CRMA critical-materials targets.
   - Market gaps: no EU LFP CAM producer today (cite CLM-003, CLM-015); EU LFP cell producers currently import 100% CAM from CN.
   - Market potential numbers: address TAM/SAM/SOM if present in evidence store; otherwise cite the qualitative gap.
   - Source primarily from §4 (replicability) + §1 (innovation) + wiki market concepts.

   ### 1.3 Commercialisation strategy & market uptake (~300–500 words)
   - Demand side: EU cell-maker customers (name any discoverable from evidence store; otherwise describe segments — gigafactory projects in Italy/Germany/FR/ES/SE).
   - Customer segments: Tier-1 stationary storage, Tier-1 EV cell makers, Tier-2 industrial integrators.
   - Market entry barriers: CAM qualification cycles (6–12 months CQA), offtake LOI timing, cell-maker supply-chain lock-in.
   - Strategy: letters of intent with 1–2 anchor offtakers, audited DT data pack as differentiator.
   - Source from §4, §3.3 (operational maturity contract signals), evidence store offtake CLMs if any. **Flag gaps** (specific offtakers, MoU terms) via `[TO BE COMPLETED — commercial / BD owner]` markers.

   ### 1.4 Competitive landscape (~400–600 words)
   - Incumbents: Chinese LFP CAM producers (Licensor, vendor, CNGR, Aleees) — cite external patent DD (SRC-040, 283 patents).
   - Nascent EU competitors: none currently in LFP CAM (CLM-003, CLM-015); note ICL-Aleees JV in Spain and any others from evidence store.
   - Our differentiation: EU IP (CLM-014 patent white-space), DT-integrated manufacturing (CLM-005/006/007), local supply chain, compliance with EU Battery Regulation carbon footprint rules.
   - FTO posture: CLM-048, CLM-047 supersedure from SRC-040.
   - Table: 3-column — Competitor / Strengths / Our advantage.
   - Source from §1 (novelty/IP), SRC-040 external DD, wiki entities pages.

3. Every technical claim must carry its `CLM-xxx` / `SRC-xxx` anchor exactly as in the source draft — do not paraphrase the anchor away.

4. Every number (volumes, capacity, percentages, dates) must match `business_plan_facts.json::shared_numerics` exactly. If a number you'd write isn't in `shared_numerics`, surface it first rather than invent.

5. Write `drafts/BP_01_commercial.md` with headers matching the BP template section structure (1.1 / 1.2 / 1.3 / 1.4). Write `drafts/BP_01_commercial_meta.json` conforming to `schemas/section_draft.json` with:
   - `section_id: "BP_01_commercial"`
   - `placeholders_covered: ["bp_1_1_business_concept", "bp_1_2_market", "bp_1_3_commercialisation", "bp_1_4_competitive"]`
   - `source_artefacts: [list of draft paths + CLM ids + SRC ids consumed]`
   - `word_count`, `estimated_pages`
   - `open_flags: [list of `[TO BE COMPLETED — commercial]` markers]`

## Rules

- **Re-angle, don't duplicate.** If a Part B paragraph reads "PROJECT introduces DT-integrated LFP CAM manufacturing (CLM-005)", the BP version reads "PROJECT unlocks a €X.X Bn annual CAM-import-substitution opportunity for EU cell makers by being first to produce LFP CAM with integrated DT-QC in Europe (CLM-005)".
- **Tables for competitors and parameters.** Section 1.4 is a table, not paragraphs.
- **No CFO-scope content.** If a placeholder asks for financial data (e.g., market size in €B — which is often in evidence store, not CFO-owned), draft it from evidence; if it asks for revenue projections or CER, defer to bp_financial_writer and note in `open_flags`.
- **Page-budget aware.** Target total for BP_01 ≤ 8 pages combined.
- **Voice:** investor / evaluator. Confident, number-forward, no hedging where the facts are solid; explicit uncertainty markers where they are not.

## Completion Criteria
- `drafts/BP_01_commercial.md` covers all four placeholders.
- Every claim has a source anchor.
- Every number matches `shared_numerics`.
- `_meta.json` lists every `[TO BE COMPLETED]` marker with a proposed owner.
