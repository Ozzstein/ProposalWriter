# Revision Plan — FAAM-ENI Circular Energy

**Generated**: 2026-04-05
**Predicted score**: 62/105 (59%) — realistic scenario
**Funding probability**: At risk (needs top-quartile; currently second/third)
**Hard rejection risks**: 4 detected (2 critical, 2 medium-high)
**Deadline**: 23 April 2026 (18 days remaining)

---

## CRITICAL — Must Fix Before Submission (Rejection Risk)

### C1. Complete Section 3.2 Financial Maturity [CFO TEAM]
**Impact**: Cascade gate — automatic rejection if missing
**Score at stake**: 10 weighted points (5 raw × 2 weight)
**Action**: CFO team must draft: CAPEX breakdown, financing plan (debt/equity), WACC, IRR/NPV (pre/post grant), sensitivity analysis, Eni equity commitment, lender engagement evidence
**Owner**: CFO + external company

### C2. Complete Section 5 Cost Efficiency [CFO TEAM]
**Impact**: Cascade gate — automatic rejection if ratio > 200 EUR/tCO2 or section missing
**Score at stake**: 15 weighted points
**Action**: Complete relevant cost calculator, calculate cost efficiency ratio, draft Section 5.1
**Owner**: CFO + external company

### C3. Complete GHG Calculator + Sections 2.1 and 2.2 [CFO TEAM]
**Impact**: Cascade gate on quality (min 3/5); relative avoidance must be ≥50%
**Score at stake**: 12 weighted points
**Action**: Complete all sheets of GHG calculator with data traceability. Draft narrative for 2.1 (absolute) and 2.2 (relative). NOTE: 189 m³ gas/t complicates the calculation — ensure temporal averaging over 10 years from ~2029 captures the grid decarbonization trajectory.
**Owner**: CFO + external company

### C4. Complete Mandatory Annexes [CFO TEAM + COORDINATION]
**Impact**: Inadmissible without them — automatic rejection
**Missing**: Business plan (60pp), financial model, GHG calculator, relevant cost calculator, shareholders financial resources, funding support docs, supply contract docs, Gantt chart
**Owner**: CFO + project team

---

## HIGH PRIORITY — Significant Score Impact (Our Technical Sections)

### H1. Fix Electrification Narrative Inconsistency
**Source**: Scientific review + evaluator simulation
**Issue**: Text oscillates between "fully electrified" and "progressively electrified." The actual electrification percentage is never stated.
**Action**:
1. Calculate the exact energy split: electricity (3,580 kWh) vs gas (189 m³ ≈ 1,890 kWh thermal) per tonne
2. State clearly: "~65% of process energy is electrical at entry into operation" (or whatever the actual figure is)
3. Add a quantified electrification roadmap table: % electric at EiO, Year 3, Year 5, Year 10
4. Update ALL sections (00, 01, 02.3, 04, abstract, FS) for consistency
**Impact**: +0.5-1.0 points on Innovation (×2 = +1-2 weighted)
**Owner**: Technical team

### H2. Address FIB/FAAM CAM Synthesis Experience Gap
**Source**: Scientific review
**Issue**: FIB has 50 years in lead-acid and Li-ion cell/pack assembly but zero experience in CAM powder synthesis (spray drying, calcination, milling). No technology licensor or process know-how transfer is identified.
**Action**:
1. Identify a technology partner or licensor for LFP CAM synthesis know-how (even if not a formal consortium partner — can be a subcontractor or technology provider)
2. Add to Section 0.2 and 3.3e: process engineering recruitment plan or technology licensing agreement
3. Strengthen by noting Eni's chemical process engineering expertise as a mitigation
**Impact**: +0.5-1.0 on Technical Maturity (×2) and Operational Maturity (×2) = +2-4 weighted
**Owner**: User / FIB

### H3. Harmonize CQA Specifications Across All Documents
**Source**: Scientific review
**Issue**: D50 varies (0.7-2.5 μm vs 1-3 μm), carbon content varies (1.0-1.8% vs 1.5-3.0%), SSA varies (10-14 vs 12-18 m²/g)
**Action**: Use the production document specifications as the single source of truth:
- D50: 0.7-2.5 μm, SSA: 10-14 m²/g, Carbon: 1.0-1.8%, Moisture: <750 ppm
- Search and replace ALL instances across ALL files
**Impact**: Prevents evaluator confidence erosion
**Owner**: Technical team

### H4. Add DT Development Timeline with Intermediate Milestones
**Source**: Scientific review + evaluator simulation
**Issue**: TRL 3-4 → 6-7 in 4 years is under-justified. No intermediate milestones or comparable precedent cited.
**Action**: Add a DT development milestone table to Section 3.1:
- M6: Data architecture and sensor specification complete
- M12: First physics-based model (calcination CFD) validated on vendor test data
- M18: Surrogate model library built, edge computing infrastructure deployed
- M24: Layer 2 (DCDC) operational — all sensors streaming to DT platform
- M36: Layer 3 (Core DT) operational — closed-loop MPC for calcination demonstrated
- M42: Full ISO 23247 Layer 4 integration, QbD/PAT framework operational
- M48: DT validated on first production batches at EiO
**Impact**: +0.5 on Technical Maturity (×2 = +1 weighted)
**Owner**: Technical team

### H5. Complete Sections 8 and 9 (Boilerplate)
**Source**: Compliance review
**Issue**: Ethics, Security, and Declarations sections not written
**Action**: Write standard boilerplate for 8.1 (N/A), 8.2 (N/A), 9 (all declarations — DNSH, double funding, PDA YES, national schemes YES, Member States YES)
**Impact**: Compliance — prevents rejection
**Owner**: Technical team (5 minutes)

---

## MEDIUM PRIORITY — Score Improvement

### M1. Add Named Key Personnel (at least role descriptions)
**Issue**: Section 3.3e lists roles but no named individuals
**Action**: At minimum, add role descriptions with required qualifications. Add CVs when available. List FIB's history of PhD/MSc support.
**Impact**: +0.5 on Operational Maturity

### M2. Strengthen University Collaboration Section
**Issue**: PoliMi and PoliTo listed as "candidates" — sounds tentative
**Action**: If any preliminary contact has been made, upgrade to "in discussion." Add specific research groups (SuPER team at PoliMi, GAME Lab at PoliTo) with their relevant publications.
**Impact**: +0.5 on EU Leadership

### M3. Add Electrification Roadmap to Abstract
**Issue**: Abstract must be updated after electrification narrative correction
**Action**: Replace "fully electrified" language with quantified electrification % and trajectory
**Impact**: First impression for evaluators

### M4. Add Contingency Budget Line
**Issue**: No contingency percentage mentioned in workplan
**Action**: Add 10-15% contingency to budget discussion (even if specific numbers are TBC)
**Impact**: Credibility for Financial Maturity

### M5. ETS Benchmark Resolution
**Issue**: Section 2.3.2 has [TO BE COMPLETED] on ETS benchmark applicability
**Action**: Determine if LFP CAM has a direct benchmark. If not, state clearly that no applicable benchmark exists and cite the regulation.
**Impact**: Prevents cascade gate issue on GHG Quality

---

## LOW PRIORITY — Polish

### L1. Remove any remaining "fully electrified" language (search all files)
### L2. Add cross-references between Part B sections and feasibility study sections
### L3. Ensure all figure references (Figure 1, 2, etc.) have consistent numbering
### L4. Add Gantt chart annex reference with timeline visual
### L5. Final proofread for terminology consistency (saggars vs crucibles, etc.)

---

## Responsibility Summary

| Items | Owner | Deadline |
|-------|-------|----------|
| C1-C4 (financial, GHG, annexes) | CFO + external company | April 18 (5 days before deadline) |
| H1, H3, H4, H5 (electrification, CQA, DT milestones, boilerplate) | Technical team (us) | April 8 |
| H2 (CAM experience gap) | User / FIB management | April 10 |
| M1-M5 (personnel, universities, abstract, contingency, ETS) | Mixed | April 15 |
| L1-L5 (polish) | Technical team | April 20 |
