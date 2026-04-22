# BP Counterparty Writer

## Class
Writer.

## Model
sonnet

## Mission
Draft BP section 1.6: (a) Project diagram brief, (b) Description of project counterparties, (c) Robustness and strategy to secure contracts. This section is uniquely BP-scope — Part B does not cover counterparty relationships with the same depth, so this worker does more new writing than the other commercial writer.

## Inputs
- `intermediate/business_plan_facts.json`
- `drafts/{00_project_and_applicants,03_3_operational_maturity,07_workplan,03_4_risk_management}.md`
- `context.md` — project JV structure, EnergyCo + BatteryCo
- `memory/{evidence_store,claim_registry}.jsonl`
- `inputs/Tpl_Business Plan (INNOVFUND).rtf`

## Steps

1. Read `business_plan_facts.json::placeholders` for prefix `bp_1_6_*`.

2. Draft each sub-section:

   ### 1.6.a Project diagram (description + figure brief)
   The BP template expects an inserted project diagram. This worker does NOT render the diagram — it produces:
   - A ~100-word introductory paragraph describing the diagram's scope (every party + every contractual relationship).
   - A **figure brief** for `/figures` recorded as `F-07-project-diagram` in `figures_register.md` (append) and in this section's `_meta.json::figure_briefs[]`. Brief must specify:
     - Nodes: EnergyCo S.p.A., BatteryCo S.p.A. / BatteryCo, project JV (project vehicle — confirm via CFO whether SPV or not), EPC contractor (TBD), Licensor licensor, Tier-1 offtaker(s) (TBD — BD), O&M contractor (TBD), equipment suppliers (vendor, internal Licensor-design build), electricity provider (TBD — PPA), feedstock suppliers (Li2CO3, FePO4 — TBD), advisors (legal, financial, technical), insurers (TBD), CINEA (grantor), regional authority + national ministry (permits).
     - Edges: equity flows, shareholder loan (if any), EPC contract, offtake LOIs, technology licence, grant disbursement, permit approvals.
     - Highlight SPV if one exists.
     - Style: Mermaid diagram or structured node-edge list; graphics orchestrator will render with the concept_image_generator or plot_renderer.
   - An explicit `[FIGURE PENDING — F-07 via /figures]` marker inline in the draft.

   ### 1.6.b Description of project counterparties (~600–800 words)
   For each counterparty, one paragraph of: who they are, role in the project, technical/financial/commercial standing, credit rating where available.

   - **Sponsors / shareholders:**
     - EnergyCo S.p.A. — Italian integrated energy major, public-equity listed (BIT:ENERGYCO). Role: majority(?) shareholder of project JV, site provider (the plant site brownfield), grant applicant coordinator. Financial standing: `[CFO — reference EnergyCo consolidated 2023–2025 annual report]`.
     - BatteryCo S.p.A. / BatteryCo (parent group) — Italian battery-systems manufacturer. Role: minority(?) shareholder of project JV, LFP expertise holder, commercial channel. Financial standing: `[CFO — reference BatteryCo financial statements]`.
   - **Project company:** project JV (the JV) — mono-beneficiary per `state.json`. Legal form / jurisdiction / capital structure: `[TO BE COMPLETED — Legal]`.
   - **Off-takers:** `[TO BE COMPLETED — Commercial / BD — expected anchor offtaker(s), LOI status]`. Note: target segments defined in BP 1.3 but specific counterparties are the BD team's to supply.
   - **EPC / construction contractor:** `[TO BE COMPLETED — Procurement — EPC firm shortlist, state of tender]`. Long-lead items per `drafts/07_workplan.md::WP1 A1.4` (calcination furnace 9–12mo, spray dryer 6–9mo).
   - **Technology licensor:** the Licensor — Chinese LFP CAM producer, licensor of the reference process design used as CAPEX/OPEX benchmark (SRC-037, CLM-039). Technical standing: proven 50 kt/yr + scale operator. Licence terms: `[TO BE COMPLETED — Legal — licence agreement terms, IP scope, residual-value treatment]`.
   - **Equipment suppliers:** vendor (reference-design equipment supplier per CAPEX.xlsx benchmark columns), plus Italian/EU suppliers to be selected per procurement.
   - **O&M / operator:** `[TO BE COMPLETED — Operations — operator identity, SLA scope]`.
   - **Electricity / utilities:** `[TO BE COMPLETED — Commercial — PPA counterparty, Italian industrial electricity (€130/MWh working assumption)]`.
   - **Feedstock suppliers:** Li2CO3 (global commodity; Tianqi / Albemarle / SQM / Ganfeng are the Tier-1 options) + FePO4 (European sources?). `[TO BE COMPLETED — Procurement]`.
   - **Advisors:** Legal, financial, technical — `[TO BE COMPLETED]`.
   - **Insurers:** `[TO BE COMPLETED]`.
   - **Lenders:** `[TO BE COMPLETED — CFO — see RC_Calculator_ROADBLOCKERS.md §A3, A4]`.
   - **Grantor:** CINEA (EU Innovation Fund executive agency) — INNOVFUND-2025-NZT-CLEAN-TECH-MANUFACTURING call.
   - **Permitting authorities:** Regione Puglia (VIA, AIA), Comune di the plant site (building permit), MASE (if escalated nationally). Per `drafts/07_workplan.md::WP1 A1.3`.

   Credit ratings: where EnergyCo/BatteryCo have public credit ratings (Moody's / S&P / Fitch), cite the latest from evidence store if present; otherwise `[TO BE COMPLETED — CFO to provide latest published rating]`.

   ### 1.6.c Robustness and strategy to secure contracts (~400–600 words)
   For each contract class, state: indicative terms where known, MoU/LoI status, and the strategy to reach execution by FC.

   - **Offtake agreements:** `[TO BE COMPLETED — Commercial — anchor LoI target names + volume + pricing mechanism + term length (5–7 yr typical); LoI signing target before FC per `drafts/03_3_operational_maturity.md` if referenced there]`.
   - **Supply agreements (Li2CO3, FePO4):** `[TO BE COMPLETED — Procurement — target suppliers + pricing mechanism (indexed vs fixed) + term]`.
   - **Electricity PPA:** `[TO BE COMPLETED — Commercial — PPA counterparty, renewable/green attribute, term, price mechanism; note: Italian industrial rate working assumption €130/MWh]`.
   - **EPC contract:** `[TO BE COMPLETED — Procurement — EPC firm identity, lump-sum vs. cost-plus, liquidated damages, performance guarantees]`. Procurement strategy per `drafts/07_workplan.md::WP1 A1.4`.
   - **Technology licence:** Licensor — `[TO BE COMPLETED — Legal — licence-agreement state, terms]`.
   - **O&M contract:** `[TO BE COMPLETED]`.
   - **Construction insurance / performance bonds:** `[TO BE COMPLETED — Insurance advisor]`.
   - **Strategy-to-secure summary:** narrate the critical path — offtake LoIs at FC, supply LoIs at FC, EPC signed at or before FC, licence signed before FC, PPA signed before EiO. Cite `drafts/07_workplan.md` milestones. Tie to the FC-date risk discussion in `drafts/03_4_risk_management.md` (R13 IP/FTO, others).

3. Write `drafts/BP_03_counterparties.md` with the three sub-section headings. Write `_meta.json` with:
   - `section_id: "BP_03_counterparties"`
   - `placeholders_covered: ["bp_1_6_diagram", "bp_1_6_description", "bp_1_6_robustness"]`
   - `figure_briefs`: the F-07 project diagram brief (detailed) — ready to hand to `/figures`
   - `open_flags`: every `[TO BE COMPLETED]` marker tagged with proposed owner (Commercial / Procurement / Legal / CFO / Operations / Insurance)
   - `word_count`, `estimated_pages`

## Rules

- **Structured ownership.** Every `[TO BE COMPLETED]` marker names the specific owner team (not just "TBD").
- **No invented counterparties.** Do not guess at EPC firm or offtaker names — leave stubs with proposed owner.
- **Consistency with Part B.** EnergyCo/BatteryCo description, site (the plant site brownfield), mono-beneficiary structure all come from `state.json` + `drafts/00_project_and_applicants.md`. Do not re-describe differently.
- **Licence posture.** Licensor licensor is a real counterparty per §1 and SRC-037 — describe its role factually; do not gloss the IP dependency.
- **Figure is a brief, not a render.** Do not attempt to draw the project diagram — emit a structured brief for `/figures` F-07.

## Completion Criteria
- `drafts/BP_03_counterparties.md` covers 1.6.a/b/c.
- F-07 figure brief recorded in both the section `_meta.json::figure_briefs` and appended to `drafts/figures_register.md`.
- All open items have a named owner team.
