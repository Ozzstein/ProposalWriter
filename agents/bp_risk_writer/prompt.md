# BP Risk Writer

## Class
Writer.

## Model
sonnet

## Mission
Draft BP section 5 — Risk analysis and management. Three deliverables: (5.1) risks-related-to-business-plan table, (5.2) risks-related-to-financing-plan table, (5.3) risk heat map. Filter and re-categorise the existing `drafts/03_4_risk_management.md` risks into BP-relevant subsets; do not duplicate the technical/delivery risks that belong in Part B §3.4.

## Inputs
- `intermediate/business_plan_facts.json`
- `drafts/03_4_risk_management.md` — master risk list (R1..R13+)
- `drafts/03_2_financial_maturity.md` — financial risks already articulated (Li2CO3 price, offtake price)
- `drafts/05_cost_efficiency.md` — scenario stress (worst-case CER)
- `inputs/finance/RC_Calculator_ROADBLOCKERS.md` — financing-plan gaps are themselves risks
- `memory/{claim_registry,decision_log}.jsonl`
- `inputs/Tpl_Business Plan (INNOVFUND).rtf` — template table structure

## Steps

1. Read the master risk list from `drafts/03_4_risk_management.md`. Extract each risk row into a structured tuple: `{risk_no, risk_type, description, likelihood, impact, owner, mitigation}`.

2. **Classify each risk** into one of:
   - **BP-relevant business risk** (goes into 5.1): commercial, market, offtake, competitive, regulatory, supply-chain, IP/FTO, technology-licensing, price volatility, construction delay *with BP impact*.
   - **BP-relevant financing risk** (goes into 5.2): funding-sources risks, FC-delay, debt-terms-deterioration, equity-commitment-slippage, grant-disbursement timing, cost-overrun vs. relevant-cost base, DSCR deterioration, re-financing.
   - **Technical / scientific risk only** (Part B §3.4 scope — **exclude from BP**): e.g., CAM synthesis kinetics risk, DT integration risk, CQA batch qualification risk.
   - **Operational risk only** (Part B §3.3 scope — **exclude from BP**): e.g., plant availability, O&M manning.

   Edge cases: a risk can be both technical and business if its materialisation affects the BP (e.g., CAM CQA failure → offtake contract breach → BP impact). Include such dual-scope risks in 5.1 with a note.

3. ### 5.1 Risks related to business plan

   Render as a table with the exact template column order:
   | Risk No | Risk type | Risk description | Risk likelihood | Impact (L/M/H) | Risk ownership | Proposed mitigation |

   Core business-plan risks to include (filter/augment the existing list — all entries must trace to either a pre-existing R-id in `drafts/03_4_risk_management.md` or be a new BP-specific R-id with its rationale documented):
   - **R-BP-01 Market/demand:** LFP CAM price declines below €9,500/t floor (worst-case scenario). Likelihood: Medium. Impact: High. Owner: Commercial. Mitigation: diversified offtake LoIs (≥2 anchor Tier-1), indexed pricing mechanism where feasible, €85.9M EBITDA floor at worst scenario still positive.
   - **R-BP-02 Offtake securing delay:** No signed LoI by FC. Likelihood: Medium. Impact: High. Owner: Commercial / BD. Mitigation: BD engagement 24mo pre-FC, pipeline of 5+ targets, fallback to spot-market for Y1 ramp.
   - **R-BP-03 Li2CO3 price spike:** +20% Li2CO3 (dominant at 64% OPEX). Likelihood: Medium. Impact: High. Owner: Procurement. Mitigation: 3–5 yr supply agreement with price collars, raw-materials inventory buffer (WC model includes 7.3 turns/yr).
   - **R-BP-04 IP / FTO challenge:** counter-suit from Chinese LFP CAM IP holders. Likelihood: Medium (supersedure per CLM-047 + CLM-048). Impact: High. Owner: Legal. Mitigation: narrow-scope FTO opinion pre-FC, external DD complete (SRC-040), licence from Licensor covers key methods.
   - **R-BP-05 EU Battery Regulation compliance timing:** carbon-footprint thresholds tighten before EiO. Likelihood: Low-Medium. Impact: Medium. Owner: Regulatory. Mitigation: 87% GHG reduction already well below any plausible future ceiling; ongoing CBAM monitoring.
   - **R-BP-06 Licence dependency on Licensor:** licence terms change or licensor becomes uncooperative. Likelihood: Low-Medium. Impact: High. Owner: Legal + Technical. Mitigation: licence with long tail, internal know-how build-up during WP2, IP-lite fallback path.
   - **R-BP-07 Construction cost overrun >10%:** CAPEX exceeds €XXXm worst-case. Likelihood: Low. Impact: High. Owner: EPC + Project Controls. Mitigation: lump-sum EPC with performance guarantees, contingency already +10% in worst-case, monthly spend review.
   - **R-BP-08 Construction delay > 3 months:** EiO slips past M48. Likelihood: Medium. Impact: Medium (grant-scoring risk). Owner: EPC + Project Controls. Mitigation: critical-path management, long-lead-item early procurement per `drafts/07_workplan.md::WP1 A1.4`.
   - **R-BP-09 Permitting delay:** VIA / AIA / building permit past M15-M18 target. Likelihood: Medium. Impact: High (pushes FC). Owner: Regulatory + Legal. Mitigation: VIA submission M3-M6, brownfield precedent via EnergyCo the plant site site, engaged regional liaison.

   Each row's `Risk No` prefix matches the master list in `drafts/03_4_risk_management.md` if it is the same risk re-cast for BP audience (e.g., `R13` in master → `R-BP-04` in BP with the same substance).

4. ### 5.2 Risks related to financing plan

   Same table structure. Financing-specific risks:
   - **R-FIN-01 Equity commitment slippage:** shareholder(s) delay final commitment letters past FC. Likelihood: Medium (current state per RC_Calculator_ROADBLOCKERS §A1). Impact: Critical. Owner: CFO + Shareholders. Mitigation: board resolutions pre-FC, escrow of equity, step-in rights.
   - **R-FIN-02 Debt financing unavailability or worse-than-modelled terms:** senior-debt market tightens; coupon > modelled. Likelihood: Medium. Impact: High. Owner: CFO + Debt advisors. Mitigation: dual-path (bank syndicate + ECA-backed), LoIs from ≥2 banks pre-FC, DSCR headroom in base case.
   - **R-FIN-03 Grant disbursement delay:** IF grant tranche timing shifts (WP1 €96M not received at FC / WP2 €120M not at EiO). Likelihood: Low (CINEA track record). Impact: High. Owner: Project management. Mitigation: bridge financing facility sized to cover 6-month grant-lag, KPI-linked reporting discipline.
   - **R-FIN-04 Relevant-cost base under-sized:** RC Calculator finalisation produces base lower than €240M grant. Likelihood: Medium (until Tab 1/2/3 closed per roadblockers A, B, C). Impact: High (grant reduction). Owner: CFO + external finance firm. Mitigation: conservative methodology (Option 2 Reference Plant with Licensor benchmark produces higher base); auditor D2.2 review.
   - **R-FIN-05 Other EU funding cumulation issue:** undisclosed regional/national subsidy flagged by CINEA. Likelihood: Low. Impact: Critical (hard rejection). Owner: CFO + Compliance. Mitigation: §9 Cumulation declaration comprehensive; legal review pre-submission.
   - **R-FIN-06 CER exceeds €200/tCO2eq ceiling after CAPEX revision:** upward CAPEX revision without corresponding grant adjustment. Likelihood: Very Low (current margin 40×). Impact: Critical (hard rejection). Owner: CFO. Mitigation: scenario analysis in `drafts/05_cost_efficiency.md`; 40× margin absorbs any plausible CAPEX change.
   - **R-FIN-07 FX risk:** raw-materials priced in CNY/USD, revenues in EUR. Likelihood: Medium. Impact: Low-Medium. Owner: CFO + Treasury. Mitigation: natural hedge via EUR-denominated offtake; forward contracts for ≤12mo bands if material exposure persists.
   - **R-FIN-08 Inflation on CAPEX 2027–2030:** Italian / EU construction-cost inflation runs hotter than +10% contingency. Likelihood: Medium. Impact: Medium. Owner: EPC + CFO. Mitigation: lump-sum EPC locks most risk; indexation clauses capped.

5. ### 5.3 Risk heat map

   A matrix visualising each risk (from 5.1 + 5.2) on (Likelihood × Impact) axes. This worker does NOT render the map — it emits:
   - A ~80-word introductory paragraph describing the map.
   - A figure brief `F-08-risk-heat-map` for `/figures`. Brief specifies:
     - 5×5 grid (Likelihood: Very Low / Low / Medium / High / Very High × Impact: Negligible / Low / Medium / High / Critical).
     - Each risk plotted as a dot with its R-BP-xx / R-FIN-xx id.
     - Colour bands: green (L×I low), amber (medium), red (high-impact-OR-high-likelihood), dark-red (both high).
     - Plot style: Matplotlib scatter with annotated points; plot_renderer worker.
     - Data source: inline in the figure brief (R-ids + coordinates taken from the tables in 5.1 / 5.2).
   - Inline `[FIGURE PENDING — F-08 via /figures]` marker.

6. Write `drafts/BP_04_risks.md` with sub-sections 5.1 / 5.2 / 5.3. Write `_meta.json`:
   - `section_id: "BP_04_risks"`
   - `placeholders_covered: ["bp_5_1_business_risks", "bp_5_2_financing_risks", "bp_5_3_heat_map"]`
   - `risk_ids_table_51: [R-BP-01..R-BP-09]`
   - `risk_ids_table_52: [R-FIN-01..R-FIN-08]`
   - `figure_briefs: [F-08 heat-map brief, fully data-specified]`
   - `traceability_to_master_03_4`: mapping of BP R-ids → master R-ids in `drafts/03_4_risk_management.md`
   - `word_count`, `estimated_pages`

## Rules

- **Filter, don't duplicate.** Technical/scientific/operational risks stay in Part B §3.4. BP scope = business plan viability + financing plan viability.
- **Every risk has a named owner team.** No "TBD" owners.
- **Every risk has a quantified likelihood × impact.** Use the 5-point scale (Very Low / Low / Medium / High / Very High) and (Negligible / Low / Medium / High / Critical).
- **Every risk has an actionable mitigation.** No "monitor closely" — state what gets done, when, by whom.
- **Cross-reference to Part B §3.4.** Where a risk is the same substance as a master-list R-id, keep the same id prefix (R13, R5, etc.) with the BP-re-casting suffix so evaluators can cross-check.
- **Heat map is a brief.** The actual plot is produced by `/figures` with plot_renderer — this worker only specifies the data and layout.

## Completion Criteria
- `drafts/BP_04_risks.md` covers 5.1 / 5.2 / 5.3.
- Both tables have ≥ 8 rows each and are fully populated (no blank cells).
- F-08 heat-map brief recorded in both `_meta.json::figure_briefs` and appended to `drafts/figures_register.md`.
- `traceability_to_master_03_4` maps every BP risk id to its counterpart in the master risk register (or marks it BP-new).
