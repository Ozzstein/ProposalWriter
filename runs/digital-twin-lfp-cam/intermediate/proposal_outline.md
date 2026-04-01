# Proposal Outline — digital-twin-lfp-cam
# Innovation Fund Full Application (Part B)
# Topic: INNOVFUND-2025-NZT-CLEAN-TECH-MANUFACTURING

**Template source**: `inputs/application-form_innovfund_en.pdf` (INNOVFUND V5.0, 01.12.2025)
**Page limit**: 70 pages (Part B only; annexes do not count)
**Deadline**: 23 April 2026 — 17:00 CET

---

## Page Budget

| Section | Target pages | Notes |
|---|---|---|
| Cover + Summary | 1 | Fixed format |
| 0. Project and Applicants | 4–5 | Background, consortium, site, technology |
| 1. Degree of Innovation | 10–12 | Highest weight (×2) — most important |
| 2. GHG Emission Avoidance | 8–10 | Hard thresholds — must be rigorous |
| 3. Project Maturity | 14–16 | Second highest weight (×2 per sub) |
| 4. Replicability | 6–8 | EU leadership sub-criterion is 10pts |
| 5. Cost Efficiency | 3–4 | Formulaic; quality of methodology matters |
| 6. Bonus Points | 1 | Briefly explain not applicable |
| 7. Workplan / Work Packages | 10–12 | Gantt + WP tables |
| 8. Other (Ethics/Security) | 1–2 | Short but mandatory |
| 9. Declarations | 1 | Boilerplate |
| **Total** | **~58–71** | Target ~65pp to stay within limit |

---

## PROJECT SUMMARY

**File**: `drafts/00_summary.md`
**Evaluation criterion**: N/A (carries to Part A abstract — 2,000 chars)
**Content**:
- One-page summary: project title, location, technology, grant ask, GHG avoidance, key innovation claim
- Must be accessible to non-specialists
- Mirror text to Part A abstract field (2,000 character limit)

---

## SECTION 0 — Project and Applicants

**File**: `drafts/00_project_applicants.md`
**Evaluation criterion**: No direct score — sets context for all evaluators
**Subsections** (per official template):

### 0.1 Background and Objectives
- LFP battery market context and EU strategic importance (CRMA, EU Battery Regulation)
- Gap: no integrated Digital Twin for LFP CAM powder manufacturing exists (cite Section 10.1 of research report)
- Project objectives: develop, deploy and validate ISO 23247 four-layer DT at FAAM Brindisi plant
- Specific objectives (SMART): quantified CQA improvements, energy reduction, scrap reduction targets

### 0.2 Consortium: Beneficiaries and Other Participants
- FAAM (joint venture of FIB S.p.A. + Eni): lead applicant
  - FIB S.p.A.: Italian battery manufacturer (founding year, employees, expertise)
  - Eni: Italian energy major (founding year, employees, relevant expertise in industrial process digitalization)
- Why FAAM is best placed: industrial-scale LFP manufacturing planned; Eni brownfield site; FIB battery expertise
- TBD research partners (Italian universities / EU RTOs)

### 0.3 Technical Characteristics and Scope
- Location: Brindisi, Italy — Eni brownfield industrial site
- Technology: LFP CAM powder synthesis (solid-state calcination route) with ISO 23247 Digital Twin overlay
- Inputs: iron precursor (Fe₂O₃ or FePO₄), lithium source (Li₂CO₃ / LiOH), phosphate source (H₃PO₄ / NH₄H₂PO₄), carbon source (sucrose/citric acid)
- Output: 7,000 t/yr battery-grade LFP CAM powder (D₅₀ 1–3 µm, phase purity >98%, C content 1.5–3.0 wt%)
- Process route: precursor mixing → spray drying → calcination (electric rotary kiln, 600–750°C) → milling (jet/ball) → classification → packaging

### 0.4 Technology Scope and Chosen Technological Solution
- Why electric calcination: maximise renewable electricity use, avoid direct fossil combustion (key for GHG case)
- Why ISO 23247 DT framework: international standard, interoperability, auditable for EU Battery Passport
- Why solid-state route: proven industrial scalability at 7,000 t/yr; sol-gel higher quality but not scalable
- Safety and reliability: PAT sensors for continuous quality verification; redundant sensor architecture; MPC fail-safe modes
- Standards: ISO 23247:2021, EU Battery Regulation 2023/1542, IEC 62443 (industrial cybersecurity for OPC-UA)

---

## SECTION 1 — Degree of Innovation

**File**: `drafts/01_innovation.md`
**Evaluation criterion**: C1 — max 30 weighted pts (15 × weight 2), min pass 9/15
**Target score**: 13/15 raw → 26/30 weighted
**Writing guidance**: This is the highest-stakes section. Every innovation claim must be backed by a claim_id from the claim registry, sourced from the evidence store.

### 1.1 Innovation in Relation to the State of the Art

#### State-of-the-Art (Commercial)
- Conventional LFP CAM production: batch solid-state processes with offline quality control (XRD, particle sizing)
- No closed-loop, real-time control of CQAs in commercial LFP powder manufacturing
- Manual operator decisions for calcination temperature profile and milling duration
- Batch-to-batch variability: industry standard ~±15% on D₅₀, ~±3% on phase purity (cite if available)

#### State-of-the-Art (Technological / DT Research)
- ARTISTIC platform (Franco et al., ECS 2023/2025): DT for electrode coating and calendering — **downstream of CAM**
- DiBaZ (Fraunhofer ITWM, 2024): DT for cell assembly and formation — **downstream of CAM**
- TwinHeat (MINES Paris, 2024): generic industrial furnace DT, 10-15% energy reduction — **not LFP-specific**
- ISO 23247:2021: framework exists but no reference implementation for LFP CAM synthesis
- **Gap documented in research report Section 10.1**: no integrated DT for LFP CAM synthesis from precursors

#### Innovation Beyond State-of-the-Art
Cover all dimensions required by template:
- **Plant design**: four-layer ISO 23247 architecture integrating PAT sensors directly into control loop
- **Operating approach**: closed-loop MPC of calcination and milling — first implementation in LFP CAM
- **Construction**: no special construction innovation (electric kiln is commercially available)
- **Performance/quality**: >40% reduction in batch-to-batch CQA variability; 30-50% reduction in time-to-specification
- **Reliability and availability**: Bayesian model updating ensures DT accuracy improves with each batch (not static)
- **Maintenance**: predictive maintenance capability via anomaly detection on PAT sensor streams
- **Economics**: 12-15% calcination energy reduction (from MPC optimisation); >10% scrap rate reduction

TRL trajectory:
- Physics models (CALPHAD, PBM, DEM): TRL 3-4 → TRL 7 at project end
- PAT sensor integration (Raman, FBRM): TRL 5-6 → TRL 8
- MPC/Bayesian system: TRL 4 → TRL 7
- Full integrated DT system: TRL 3 → TRL 7

Why this scale is appropriate: 7,000 t/yr is the minimum commercially-relevant scale for EU battery supply chain; sub-scale pilot would not demonstrate DT performance under real production variability

---

## SECTION 2 — GHG Emission Avoidance Potential

**File**: `drafts/02_ghg_avoidance.md`
**Evaluation criterion**: C2 — max 12 weighted pts (no weight multiplier), hard threshold sub-criteria
**Target score**: 10/12
**⚠️ Critical**: Must use official GHG calculator (Excel template). Values in this section must match Part A, Part C, and financial model.

### 2.1 Absolute GHG Emission Avoidance
- Reference scenario: conventional gas-fired rotary kiln calcination + grid electricity for milling/utilities
  - Gas consumption: [TBD — need FAAM energy data; typical ~6-10 MWh thermal/t LFP for calcination]
  - Reference grid emission factor: Italian average grid (2026 baseline)
- Project scenario: 100% electric calcination + dedicated renewable PPA
  - Emission factor: renewable PPA ~20 g CO₂/kWh (solar + wind in Puglia)
- Additional avoidances: scrap reduction (>10% fewer wasted batches = less embodied energy), spray drying electric
- Absolute avoidance [tCO₂eq over 10 years]: **[TBD — to be calculated using GHG calculator]**
- Target: ≥75,000 tCO₂eq/year → ≥750,000 tCO₂eq over 10 years

### 2.2 Relative GHG Emission Avoidance
- Formula: project_emissions / reference_emissions × 100%
- Target: >75% relative avoidance (scores 3.75/5; above 50% hard threshold)
- Sensitivity: low/central/high scenarios for grid emission factor and capacity factor

### 2.3 Minimum Requirements

#### DNSH — Climate Change Mitigation TSC
- Identify applicable Delegated Regulation activities for LFP battery component manufacturing
- Demonstrate compliance with quantitative emission limits per applicable TSC
- No significant harm to climate change mitigation objective

#### ETS Benchmark
- LFP powder manufacturing: check whether an ETS product benchmark applies
- [TBD: verify with ETS implementing regulation — likely falls under 'other products' category]
- Demonstrate that project process emissions per unit product are below applicable benchmark

#### Biomass Sustainability
- Not applicable (no biomass used in LFP manufacturing process)

---

## SECTION 3 — Project Maturity

**File**: `drafts/03_project_maturity.md`
**Evaluation criterion**: C3 — max 30 weighted pts (5pts × weight 2 per sub-criterion), min pass 3/5 each
**Target score**: 4/5 per sub-criterion → 24/30 weighted
**Mandatory annexes**: Feasibility study (60pp max), Business plan (60pp max), detailed financial model (Excel)

### 3.1 Technical Maturity

#### Technical Maturity Overview
- Attach feasibility study (mandatory)
- Current project development stage: pre-FEED / early FEED

#### Technical Feasibility (from feasibility study)
- Process description with block flow diagrams
- Unit operations: precursor mixing, spray drying, rotary kiln calcination, jet/ball milling, air classification
- Technical and operational requirements per unit operation
- Technology readiness levels (component-by-component)
- Process flow diagrams
- Mass and energy balances
- CQA targets and sensor measurement architecture
- DT system architecture (four layers per ISO 23247)

#### Due Diligence Reports
- Reference any third-party technical assessments available
- TBD: commission independent technical review of DT architecture

### 3.2 Financial Maturity

#### Project Business Plan (summary — full in annex)
- Product: battery-grade LFP CAM powder, 7,000 t/yr
- Market: European battery cell manufacturers (AESC, Northvolt, ACC, Stellantis, etc.)
- Revenue: LFP CAM spot + long-term offtake contracts (target: 60% of capacity under offtake)
- CAPEX: €250,000,000 (breakdown: process equipment, DT system, civil works, contingency)
- OPEX: [TBD — electricity, precursors, labour, maintenance, DT licensing]
- Key financial metrics table

#### Cash Flow Projections
- Project IRR without IF grant: [TBD — must show negative/suboptimal to justify additionality]
- Project IRR with IF grant: [TBD — must show viable but not excessive]
- WACC calculation
- Sensitivity analysis: LFP price ±20%, CAPEX ±15%, electricity price ±30%

#### Financing Plan
- CAPEX €250M: equity (Eni/FIB S.p.A.) + senior debt + IF grant (max €150M = 60%)
- Grant allocation: capital cost increment attributable to DT + electric kiln premium vs gas baseline
- Other public support: PNRR Italy, EIB loan (if applicable)

#### Project Funders Commitment
- Eni: equity commitment (evidence: letter of support / board resolution)
- FIB S.p.A.: equity commitment
- Debt financing: indicative terms from European banks (EIB, Mediobanca, Intesa)
- Financial close target: [Q4 2027 — within 2 years of GA signature, earning bonus consideration]

### 3.3 Operational Maturity

#### Project Implementation Plan
- Phase 0 (pre-GA, 2026): FEED completion, permitting, procurement strategy
- Phase 1 (Year 1 post-GA, 2027): detailed engineering, long-lead equipment orders
- Phase 2 (Years 2-3, 2028-2029): construction, installation
- Phase 3 (Year 3-4, 2030): DT integration, commissioning, testing
- Phase 4 (operational monitoring period, 2030-2035): 5-year reporting

Timeline milestones:
| Milestone | Target date |
|---|---|
| Grant agreement signature | Q1 2027 |
| Financial close | Q4 2027 |
| Construction start | Q1 2028 |
| Kiln installation complete | Q3 2029 |
| DT system integration | Q1 2030 |
| Commissioning | Q2 2030 |
| Entry into operation | Q3 2030 |
| End of monitoring period | Q3 2035 |

#### Permits, Rights, Licences
- Brindisi brownfield site: existing Eni industrial zoning (advantage over greenfield)
- Environmental Impact Assessment: [status TBD — confirm whether in progress]
- Building permits: Comune di Brindisi application timeline
- Operating permit (AIA — Autorizzazione Integrata Ambientale): Italian VIA process
- Public acceptance: Brindisi industrial zone (established industrial context)
- IP: DT software models owned by FAAM; open-source components (OpenFOAM) identified

#### Project Management Team
- Project Director: [TBD — Eni/FIB nominee]
- DT Technical Lead: [TBD — partner university nominee]
- Process Engineering Lead: FIB S.p.A.
- EPC Contractor: [strategy: open tender via EU procurement]
- O&M DT: in-house capability built during commissioning

#### Project Diagram
[Insert stakeholder diagram: EC/CINEA → FAAM → Eni (equity) + FIB S.p.A. (equity) + Lenders (debt) + EPC Contractor + Technology Partners + Raw Material Suppliers + Offtake Customers]

### 3.4 Risk Management
(Reference to business plan and feasibility study)
Key risks to mention in Part B:
- Technology risk: DT integration with novel electric kiln — **mitigation**: staged commissioning, factory acceptance tests
- Market risk: LFP price volatility — **mitigation**: long-term offtake agreements
- Permitting risk: Italian AIA timeline — **mitigation**: Brindisi brownfield reduces risk; early permit pre-consultation
- Energy price risk: electricity cost — **mitigation**: long-term renewable PPA with Eni

---

## SECTION 4 — Replicability

**File**: `drafts/04_replicability.md`
**Evaluation criterion**: C4 — max 15 weighted pts (weight 1)
**Sub-criterion C4.1b (EU industrial leadership, 10pts, min pass 4) is the dominant sub**
**Target score**: 12/15

### 4.1 Replicability

#### Efficiency Gains and Multiple Environmental Impacts
- Resource efficiency: >10% scrap reduction → less raw material waste (Li, Fe, P — all supply-chain constrained)
- LFP contains no cobalt or nickel (Critical Raw Materials Act alignment)
- Water savings from closed-loop process (washing step optimisation via DT)
- Carbon from bio-based sources (e.g. sucrose) — lifecycle carbon assessment
- Circularity: DT enables batch genealogy for closed-loop recycling (EU Battery Regulation Art. 75)

#### DNSH for Other Environmental Objectives
- **Climate change adaptation**: Brindisi industrial zone — existing flood/climate risk assessment
- **Water and marine resources**: closed-loop water treatment; no marine discharge; Brindisi coastal proximity → marine impact assessment
- **Circular economy**: DT enables Digital Product Passport (Art. 77 EU Battery Regulation); recycled content tracking
- **Pollution prevention**: rotary kiln gas emissions (NOx, particulates from carbon source combustion) → electric kiln eliminates combustion emissions
- **Biodiversity**: brownfield site, no greenfield land conversion

#### Contribution to Europe's Industrial Leadership and Competitiveness
- EU battery supply chain: only domestic LFP CAM producer → reduces import dependency from China
- Technology IP: DT architecture retained in EU; models published in peer-reviewed journals
- Research partnerships: Italian university (TBD), CNRS (Franco group for ARTISTIC linkage?), Fraunhofer
- Capacity building: 15+ FTE trained in DT/PAT technologies during project
- Standards contribution: ISO 23247 implementation case study for EU battery manufacturing standard
- Knowledge sharing outline: academic publications, EU Battery Alliance events, EU Battery Regulation working groups
- Supply chain due diligence: Fe, Li, P precursor sourcing audit; preference for European/North African suppliers
- European industrial ecosystems: Italian battery cluster (FIB, FAAM, other Italian cell makers)

### 4.2 Knowledge Sharing — Communication, Dissemination and Visibility
- Website: public project site with quarterly updates
- Conferences: E-MRS Spring Meeting, ISE symposium, Battery2030+ events
- Publications: open-access journal articles (at least 3 planned)
- EU Battery Passport: demonstration dataset published as open standard
- Visibility: EU flag on all materials, CINEA acknowledgement, press releases at key milestones

---

## SECTION 5 — Cost Efficiency

**File**: `drafts/05_cost_efficiency.md`
**Evaluation criterion**: C5 — max 15 weighted pts (weight 1), hard rejection if CER > €200/tCO₂eq
**Target score**: 12/15

### 5.1 Relevant Costs and Cost Efficiency Ratio
- Relevant cost methodology: Incremental cost (Option 1) — cost increment vs. gas-fired conventional plant
- Relevant costs = additional CAPEX for electric kiln + DT system vs. gas-fired baseline
  - Electric kiln premium: [TBD — typically 20-30% higher than gas-fired kiln CAPEX]
  - DT system CAPEX: [TBD — sensors, infrastructure, software development]
  - Total relevant costs: **[TBD]**
- Maximum grant: 60% of relevant costs (**not** 60% of total project CAPEX unless all CAPEX is 'relevant')
- Cost efficiency ratio = (IF grant + other public support) / absolute GHG avoidance [tCO₂eq/10yr]
- **Target ratio: < €150/tCO₂eq** (leaves margin below €200 rejection threshold)

Mandatory attachments:
- Financial information file (CAPEX inputs, RC inputs, financial model summary) — Excel template
- Detailed financial model with formulas

---

## SECTION 6 — Bonus Points

**File**: integrated into `drafts/05_cost_efficiency.md` or separate short section
- Bonus 1 (Net carbon removals): Not applicable — briefly state why
- Bonus 2 (SME): Not applicable — FAAM is not an SME (FIB + Eni are large companies)
- Bonus 3 (Maritime): Not applicable — terrestrial project

---

## SECTION 7 — Workplan, Work Packages, Activities, Milestones, Deliverables

**File**: `drafts/07_workplan.md`
**Evaluation criterion**: Part of C3 Operational Maturity
**Format**: Must use official WP tables from application form template

### 7.1 Work Plan Overview

**Work Packages:**
| WP | Title | Lead | Duration | Budget |
|---|---|---|---|---|
| WP1 | Project Management and Coordination | FAAM | Months 1–48 | TBD |
| WP2 | DT System Architecture and Model Development | FAAM + University partner | Months 1–24 | TBD |
| WP3 | PAT Sensor Integration and Validation | FAAM | Months 6–30 | TBD |
| WP4 | MPC and Bayesian Optimisation Implementation | FAAM | Months 12–36 | TBD |
| WP5 | Plant Construction and Equipment Installation | FAAM (EPC) | Months 12–42 | TBD |
| WP6 | DT Commissioning and System Integration | FAAM | Months 36–48 | TBD |
| WP7 | Monitoring, Reporting and Knowledge Sharing | FAAM | Months 42–120 (operation) | TBD |

### 7.2 Work Package Descriptions
(Use official WP template tables from application form — one table per WP)

Each WP table must include:
- WP number, title, lead beneficiary
- Objectives
- Activities (numbered)
- Milestones (with verification means and target dates)
- Deliverables (with format, dissemination, target dates)
- Resources (person-months per participant)

**Key milestones across WPs:**
| ID | Milestone | WP | Verification | Date |
|---|---|---|---|---|
| MS1 | Financial close reached | WP1 | Signed loan agreement | M12 |
| MS2 | DT architecture design frozen | WP2 | Design review document | M18 |
| MS3 | PAT sensor suite installed and calibrated | WP3 | Calibration certificate | M24 |
| MS4 | MPC controller first live run | WP4 | Control log output | M30 |
| MS5 | Plant construction complete | WP5 | Completion certificate | M42 |
| MS6 | Full DT system live at entry into operation | WP6 | Commissioning report | M48 |
| MS7 | 12-month post-operation KPI report | WP7 | Annual report to CINEA | M60 |

### Timetable (Gantt chart)
[See separate Gantt chart annex — must cover grant signature → monitoring period end]

---

## SECTION 8 — Other

**File**: integrated into `drafts/07_workplan.md` or separate

### 8.1 Ethics
- No ethics issues anticipated (industrial manufacturing project)
- No human subjects, personal data, or dual-use materials
- Confirm: no research involving animals or vulnerable populations
- Environmental ethics: full DNSH compliance (addressed in Sections 2.3 and 4.1)

### 8.2 Security
- DT system security: IEC 62443 industrial cybersecurity standard for OPC-UA/MQTT data flows
- No classified or sensitive national security information
- Process data (production volumes, formulations) treated as commercially confidential

---

## SECTION 9 — Declarations
(Boilerplate — per official template)

---

## ANNEXES

| Annex | Description | Page limit | Status |
|---|---|---|---|
| Feasibility study | Technical and financial feasibility | 60 pages | **To be commissioned** |
| Business plan | Market analysis, financial projections | 60 pages | **To be commissioned** |
| Detailed financial model | Excel with formulas | No page limit | **To be built** |
| GHG emission avoidance calculator | Excel template (official IF template) | No page limit | **To be populated** |
| Detailed budget / relevant costs calculator | Excel | No page limit | **To be built** |
| Participant information | CVs, previous projects | No page limit | **To be collected** |
| Gantt chart | Full project timeline | No page limit | **To be drawn** |
| Permits and licences | Current status documentation | No page limit | **To be obtained from FAAM** |
| Letters of support / intent | Offtake, financing, partners | No page limit | **To be obtained** |

---

## Drafts Status Tracker

| Draft file | Section | Status |
|---|---|---|
| `drafts/00_summary.md` | Project summary | Not started |
| `drafts/00_project_applicants.md` | Section 0 | Not started |
| `drafts/01_innovation.md` | Section 1 (highest priority) | Not started |
| `drafts/02_ghg_avoidance.md` | Section 2 | Not started — blocked on GHG data |
| `drafts/03_project_maturity.md` | Section 3 | Not started — blocked on feasibility study |
| `drafts/04_replicability.md` | Section 4 | Not started |
| `drafts/05_cost_efficiency.md` | Section 5 | Not started — blocked on relevant costs |
| `drafts/07_workplan.md` | Sections 7-8 | Not started |

---

## Open Items (Blocking Research and Writing)

1. **GHG data**: FAAM's reference energy consumption for calcination (MWh/t LFP) — needed for GHG calculator
2. **Grid carbon intensity**: Puglia region (ENTSO-E or Terna data for 2026 baseline)
3. **Synthesis route confirmation**: solid-state route assumed — confirm with FAAM
4. **Relevant costs breakdown**: electric kiln premium vs gas baseline; DT system cost estimate
5. **Permits status**: EIA progress for Brindisi site — confirm with FAAM
6. **Financial close timeline**: confirm whether Q4 2027 (2-year bonus) is achievable
7. **Research partners**: identify Italian university + other EU partners for Section 4
8. **Offtake agreements**: any LOI or framework agreement with battery cell makers
