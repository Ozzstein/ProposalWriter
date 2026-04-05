# 7 Workplan, Work Packages, Activities, Milestones, Deliverables and Timing

## 7.1 Work Plan Overview

The project is structured into seven mandatory sequential work packages spanning from grant agreement signature (M0, estimated Q1 2027) through the end of the 5-year operational monitoring period (M108). The work plan follows the mandatory CLEAN-TECH-MANUFACTURING WP structure: WP1 covers the period up to financial close; WP2 covers financial close to entry into operation; and WP3-WP7 cover the five years of operational monitoring and GHG emission avoidance reporting.

The timeline is designed to achieve the two key scoring milestones: **financial close within 24 months (M24)** and **entry into operation within 48 months (M48)** of grant agreement signature.

### Work Plan Summary Table

| WP | Title | Duration | Key Deliverables | Key Milestone | Payment Trigger |
|---|---|---|---|---|---|
| WP1 | Up to Financial Close | M0-M24 | D1.1-D1.7 (project management plan, financial model, KS plan, progress reports, FC documentation) | **Financial Close (M24)** | FC milestone |
| WP2 | Financial Close to Entry into Operation | M24-M48 | D2.1-D2.6 (progress reports, auditor statement, operational readiness certificate, GHG monitoring plan) | **Entry into Operation (M48)** | EiO milestone |
| WP3 | Year 1 of Operation | M48-M60 | D3.1-D3.2 (annual GHG report, updated KS report) | End of Year 1 | GHG-linked payment |
| WP4 | Year 2 of Operation | M60-M72 | D4.1 (annual GHG report) | End of Year 2 | GHG-linked payment |
| WP5 | Year 3 of Operation | M72-M84 | D5.1 (annual GHG report) | End of Year 3 | GHG-linked payment |
| WP6 | Year 4 of Operation | M84-M96 | D6.1 (annual GHG report) | End of Year 4 | GHG-linked payment |
| WP7 | Year 5 of Operation (Final) | M96-M108 | D7.1-D7.5 (annual GHG report, verified GHG report, innovation report, DNSH report, EEA content declaration) | End of Year 5 (Final) | Final GHG-linked payment |

## 7.2 Work Packages

---

### WP1: Up to Financial Close

| | |
|---|---|
| **Duration** | M0-M24 (24 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Reach financial close within 24 months of grant agreement signature through completion of detailed engineering, environmental permitting, supplier qualification, and financing agreements. |
| **Budget** | [TO BE COMPLETED: Budget to be confirmed by CFO team. Must not exceed 40% of maximum grant amount.] |

#### Activities

**A1.1 Project Management and Coordination (M0-M24)**
- Establish project management office (PMO) and governance structures (Steering Committee, Technical Committee, DT Working Group)
- Prepare detailed project management plan (M1)
- Implement project monitoring, reporting, and communication framework
- Prepare 6-monthly progress reports
- Manage Innovation Fund reporting obligations

**A1.2 Detailed Engineering (M1-M18)**
- Complete Front-End Engineering Design (FEED) covering:
  - Process flow diagrams (PFDs) and piping and instrumentation diagrams (P&IDs)
  - Equipment specification and sizing: spray dryer (electric resistance heaters, 200-250 C inlet), calcination furnace (electric roller hearth kiln or rotary kiln, 650-700 C, N2 atmosphere), jet mill, ultrasonic sieve, electromagnetic separator, packaging line
  - Site layout and building design for Brindisi brownfield location
  - Utility requirements: grid electricity supply (high-voltage connection), nitrogen generation plant (PSA or membrane), deionised water system, HVAC, compressed air
  - Integration of DT sensor infrastructure (thermocouple arrays, pyrometers, Raman probe ports, FBRM installation points, OPC-UA gateway locations) into engineering design
  - Mass and energy balance finalisation based on detailed equipment specifications
  - Hazard and operability study (HAZOP)
  - Environmental impact assessment documentation for VIA application

**A1.3 Permitting (M3-M18)**
- Submit VIA (Environmental Impact Assessment) application to Regione Puglia or MASE (M3-M6)
- Submit AIA (Integrated Environmental Authorisation) application (M6-M12)
- Submit building permit application to Comune di Brindisi (M9-M15)
- Conduct public consultation as required by Italian environmental legislation
- Respond to authority information requests
- Obtain all required permits (target M15-M18)

**A1.4 Procurement and Supplier Qualification (M6-M24)**
- Issue request for quotation (RFQ) packages for major equipment (furnace, spray dryer, milling systems, QC instruments, DCS/SCADA)
- Conduct technical evaluation and qualification of potential suppliers
- Negotiate and execute equipment supply contracts
- Place orders for long-lead items (calcination furnace: 9-12 month lead time; spray dryer: 6-9 month lead time)
- Qualify raw material suppliers (iron phosphate, lithium carbonate, glucose) with dual sourcing

**A1.5 DT Architecture Design (M6-M18)**
- Define detailed DT system architecture based on ISO 23247 four-layer model [CLM-008, SRC-007]
- Specify sensor network (types, locations, communication protocols) for each process step
- Select DT software platform and development tools (CFD solver, time-series database, ML framework, dashboard framework)
- Develop initial physics-based models using literature data and vendor test data:
  - CFD model of calcination furnace temperature distribution
  - Population balance model for milling particle size evolution
  - Multi-step reaction kinetics model for calcination (Jander/Avrami) [CLM-020]
- Design data pipeline architecture (edge-fog-cloud) with OPC-UA and MQTT protocols

**A1.6 Financial Close Preparation (M12-M24)**
- Finalise project financing structure (Innovation Fund grant + equity + debt)
- Negotiate and execute debt facility agreements
- Confirm equity commitments from FIB and Eni
- Execute key commercial agreements (off-take agreements, supply contracts). Note: primary offtake is secured internally through the co-located FIB-Eni JV battery cell and BESS factory — Eni is the guaranteed internal customer. External offtake agreements with European cell manufacturers represent additional upside.
- Coordinate timeline with the parallel development of the FIB-Eni JV battery cell and BESS factory at the Brindisi site, ensuring the CAM plant entry into operation aligns with JV factory readiness to receive LFP CAM feedstock
- Prepare and assemble all financial close documentation
- Obtain Financial Investment Decision (FID) from FIB and Eni boards

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D1.1 | Detailed project management plan | M1 | Report |
| D1.2 | Final version of the financial model | M1 | Spreadsheet |
| D1.3 | Knowledge sharing plan | M1 | Report |
| D1.4 | Knowledge sharing report | M1 | Report |
| D1.5 | Progress reports (every 6 months) | M6, M12, M18 | Reports |
| D1.6 | Updated knowledge sharing report | At FC (M24) | Report |
| D1.7 | Updated detailed project management plan | At FC (M24) | Report |
| D1.8 | Financial close documentation package | At FC (M24) | Documentation |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS1: Financial Close** | All financing agreements executed; FID taken; key permits obtained; equipment orders placed | **M24** | Signed financing agreements, board resolutions, permit decisions, equipment purchase orders |

---

### WP2: Financial Close to Entry into Operation

| | |
|---|---|
| **Duration** | M24-M48 (24 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Construct the LFP CAM manufacturing plant, develop and integrate the digital twin system, commission the facility, and achieve entry into operation within 48 months of grant agreement signature. |

#### Activities

**A2.1 Construction (M24-M36)**
- Civil works: site preparation (brownfield remediation completion if required), foundations, building construction
- Utility installation: high-voltage electrical supply, nitrogen generation plant, water treatment system, HVAC, compressed air
- Equipment installation: spray dryer, calcination furnace, jet mill, classifier, packaging line, material handling systems
- Piping, electrical, and instrumentation installation
- DCS/SCADA system installation and configuration
- Sensor network installation (thermocouples, pyrometers, Raman probes, FBRM probes, O2 sensors, flow meters)
- Coordination with parallel construction of the co-located FIB-Eni JV battery cell and BESS factory, including shared utility infrastructure and site logistics planning

**A2.2 DT System Development (M12-M42, parallel track starting in WP1)**
- Develop and validate physics-based models:
  - CFD model of electric roller hearth kiln / rotary kiln: temperature distribution, gas flow, heat transfer to crucible bed [SRC-ED-010]
  - Population balance model for jet milling: breakage kernels calibrated to milling media and LFP material properties
  - DEM model for milling media dynamics
  - Multi-step reaction kinetics model for LFP calcination: Jander + Avrami kinetics with temperature-dependent rate constants [CLM-020]
  - Spray drying model: droplet evaporation, particle morphology prediction
- Train surrogate models (PINNs, neural network emulators) on simulation datasets for real-time inference [CLM-016]
- Develop ML pipelines: anomaly detection (autoencoder), multivariate SPC, predictive quality models
- Implement data pipeline: edge gateways, OPC-UA servers, MQTT brokers, InfluxDB time-series database
- Develop Grafana dashboards and MPC operator interface
- Conduct factory acceptance testing (FAT) of DT system components

**A2.3 DT Integration and Testing (M36-M45)**
- Connect sensor network to DT data pipeline
- Verify data flow from all sensors through edge-fog-cloud architecture
- Calibrate physics-based models with commissioning data from first process runs
- Validate surrogate model accuracy against full-fidelity simulations and measured data
- Test closed-loop MPC with furnace temperature control in manual-override safety mode
- Integration testing of batch quality reporting and CQA prediction systems

**A2.4 Plant Commissioning (M36-M48)**
- Mechanical completion inspection
- Pre-commissioning checks (punch-list resolution)
- Utility commissioning: electricity supply testing, nitrogen purity verification, water quality confirmation
- Dry commissioning: individual equipment testing without process materials
- Wet commissioning: process runs with actual raw materials at reduced throughput
- Production of qualification batches: CQA verification against battery-grade specifications (D50 0.7-2.5 um, SSA 10-14 m2/g, phase purity >98% olivine, carbon 1.0-1.8 wt%, discharge capacity >=155 mAh/g at 0.1C, >=140 mAh/g at 1C, ICE ~98%, moisture <750 ppm, magnetic impurities <=1000 ppb) [CLM-009]
- Performance testing at design throughput
- Operational readiness review and certificate issuance

**A2.5 GHG Monitoring System Setup (M42-M48)**
- Install GHG monitoring instrumentation (electricity meters, process gas flow meters, material mass flow tracking)
- Establish GHG monitoring methodology and data collection protocols consistent with Innovation Fund GHG emission avoidance methodology
- Prepare GHG monitoring plan (deliverable at entry into operation)

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D2.1 | Annual progress reports | M36, M48 | Reports |
| D2.2 | Statement by independent auditor on correctness of relevant cost calculation | At EiO (M48) | Audit report |
| D2.3 | Operational readiness and completion certificate | At EiO (M48) | Certificate |
| D2.4 | Updated knowledge sharing report | At EiO (M48) | Report |
| D2.5 | Updated knowledge sharing plan | At EiO (M48) | Report |
| D2.6 | GHG monitoring plan | At EiO (M48) | Report |
| D2.7 | Updated detailed project management plan | At EiO (M48) | Report |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS2: Entry into Operation** | Plant commissioned and producing battery-grade LFP CAM; DT system operational; GHG monitoring system active | **M48** | Operational readiness certificate; qualification batch CQA results; DT system acceptance test report |

---

### WP3: Year 1 of Operation

| | |
|---|---|
| **Duration** | M48-M60 (12 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Ramp up production from commissioning rate to nameplate capacity; calibrate DT system with production-scale data; achieve expected GHG emission avoidance. |

#### Activities

**A3.1 Production Ramp-Up (M48-M54)**
- Gradual increase from commissioning throughput (25% capacity) to nameplate capacity (100%)
- Process optimisation guided by DT predictions: furnace temperature profile adjustment, spray dryer parameter tuning, milling parameter refinement
- CQA trend monitoring and batch release

**A3.2 DT Calibration and Optimisation (M48-M60)**
- Calibrate all physics-based models with production-scale data (temperature profiles, PSDs, phase purity measurements)
- Retrain surrogate models on expanded datasets including production conditions
- Activate closed-loop MPC for furnace temperature control and milling parameter adjustment
- Quantify DT value: scrap rate reduction, energy savings, batch consistency improvement vs. baseline (first commissioning batches without DT optimisation) [CLM-007]

**A3.3 GHG Monitoring and Reporting (M48-M60)**
- Continuous GHG monitoring per approved monitoring plan
- Data collection for annual GHG emission avoidance report
- Prepare annual GHG emission avoidance report

**A3.4 Knowledge Sharing (M48-M60)**
- Implement knowledge sharing plan activities: technical publications on DT implementation, participation in EU battery ecosystem events
- Update knowledge sharing report

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D3.1 | Annual GHG emission avoidance report | M60 | Report |
| D3.2 | Updated knowledge sharing report and plan | M60 | Report |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS3: End of Year 1 of Operation** | Plant operating at nameplate capacity; GHG emission avoidance documented | **M60** | GHG report; production records; CQA quality reports |

---

### WP4: Year 2 of Operation

| | |
|---|---|
| **Duration** | M60-M72 (12 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Steady-state operation; continuous DT-driven process improvement; achieve expected GHG emission avoidance. |

#### Activities

**A4.1 Steady-State Production (M60-M72)**
- Continuous production at nameplate capacity
- Ongoing CQA monitoring and batch release
- DT-guided process optimisation for yield improvement and energy reduction

**A4.2 GHG Monitoring and Reporting (M60-M72)**
- Continuous GHG monitoring
- Prepare annual GHG emission avoidance report

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D4.1 | Annual GHG emission avoidance report | M72 | Report |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS4: End of Year 2 of Operation** | GHG emission avoidance documented | **M72** | GHG report; production records |

---

### WP5: Year 3 of Operation

| | |
|---|---|
| **Duration** | M72-M84 (12 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Continued operation; GHG monitoring; DT model refinement with accumulated data. |

#### Activities

**A5.1 Production and DT Operations (M72-M84)**
- Steady-state production and continuous DT improvement
- Advanced DT applications: predictive maintenance scheduling, new-product recipe development support

**A5.2 GHG Monitoring and Reporting (M72-M84)**
- Annual GHG emission avoidance report

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D5.1 | Annual GHG emission avoidance report | M84 | Report |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS5: End of Year 3 of Operation** | GHG emission avoidance documented | **M84** | GHG report |

---

### WP6: Year 4 of Operation

| | |
|---|---|
| **Duration** | M84-M96 (12 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Continued operation; GHG monitoring. |

#### Activities

**A6.1 Production and Operations (M84-M96)**
- Steady-state production operations

**A6.2 GHG Monitoring and Reporting (M84-M96)**
- Annual GHG emission avoidance report

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D6.1 | Annual GHG emission avoidance report | M96 | Report |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS6: End of Year 4 of Operation** | GHG emission avoidance documented | **M96** | GHG report |

---

### WP7: Year 5 of Operation (Final WP)

| | |
|---|---|
| **Duration** | M96-M108 (12 months) |
| **Lead partner** | FIB (FAAM) |
| **Contributing partner** | Eni |
| **Objective** | Complete operational monitoring period; prepare final reports; demonstrate cumulative GHG emission avoidance; compile innovation and DNSH compliance evidence. |

#### Activities

**A7.1 Production and Operations (M96-M108)**
- Steady-state production operations
- Final DT performance assessment: quantified scrap reduction, energy savings, and batch consistency improvement over the 5-year monitoring period

**A7.2 Final GHG Reporting (M96-M108)**
- Annual GHG emission avoidance report (Year 5)
- Verified GHG emission avoidance report covering the entire monitoring period (M48-M108), prepared by an independent verifier

**A7.3 Innovation and Replicability Assessment (M96-M108)**
- Final report on fulfilment of claims made under Degree of Innovation (Section 1) and Replicability (Section 4) criteria
- Documentation of DT system capabilities and quantified benefits
- Assessment of technology transfer and replication potential

**A7.4 DNSH Compliance and EEA Content (M96-M108)**
- DNSH compliance report demonstrating compliance with technical screening criteria throughout project lifetime
- Declaration on equipment/components EEA-originating content (mandatory for CLEAN-TECH-MANUFACTURING)

**A7.5 Knowledge Sharing Completion (M96-M108)**
- Final updated knowledge sharing report
- Final updated knowledge sharing plan (for post-project continuation)

#### Deliverables

| ID | Deliverable | Due | Type |
|---|---|---|---|
| D7.1 | Annual GHG emission avoidance report (Year 5) | M108 | Report |
| D7.2 | Verified GHG emission avoidance report (entire monitoring period) | M108 | Verified report |
| D7.3 | Final report on innovation and replicability claims | M108 | Report |
| D7.4 | DNSH compliance report | M108 | Report |
| D7.5 | Declaration on equipment/components EEA-originating content | M108 | Declaration |
| D7.6 | Updated knowledge sharing report and plan (final) | M108 | Report |

#### Milestone

| Milestone | Description | Target | Means of Verification |
|---|---|---|---|
| **MS7: End of Year 5 of Operation (Final)** | All monitoring complete; cumulative GHG avoidance >= 75% of planned total; all final deliverables submitted | **M108** | Verified GHG report; innovation report; DNSH report; EEA declaration |

---

## Estimated Budget -- Resources

The project budget is structured to comply with Innovation Fund requirements:

- **WP1 (Up to Financial Close)**: Budget does not exceed 40% of maximum grant amount. Activities include detailed engineering, permitting, procurement, DT architecture design, and financial close preparation.
- **WP2 (Financial Close to Entry into Operation)**: Largest budget share, covering construction, equipment installation, DT development and integration, and commissioning.
- **WP3-WP7 (Operational Years 1-5)**: Budget allocation of at least 10% of maximum grant amount post entry into operation, covering production operations, GHG monitoring, knowledge sharing, and final reporting.

[TO BE COMPLETED: Specific budget figures (total CAPEX, OPEX by WP, grant request amount) to be provided by the CFO team and included in the Financial Information File (Annex 1 to Part B). The detailed budget table uses the mandatory relevant cost calculator template.]

The principal cost categories are:
- **CAPEX**: Process equipment (calcination furnace, spray dryer, jet mill, classifier, packaging), building and civil works, utility systems (electrical, N2, water), DCS/SCADA and sensor network, DT software and computing infrastructure
- **OPEX** (operational years): Raw materials (iron phosphate, lithium carbonate, glucose), electricity, nitrogen, maintenance, labour, GHG monitoring, knowledge sharing activities, final reporting and verification

**Reference**: See Financial Information File (Annex 1 to Part B) for detailed budget table and relevant cost calculation.

## Timetable

The project timetable is presented as a Gantt chart in the mandatory Timetable annex, covering the full period from grant agreement signature (M0) to end of the monitoring period (M108).

The Gantt chart shows:
- All work packages (WP1-WP7) with start and end dates
- All activities within each work package
- Dependencies between activities (critical path highlighted)
- Key milestones: Financial Close (M24), Entry into Operation (M48), End of Year 1-5
- Deliverable due dates
- Parallel tracks: DT development (M12-M42) running in parallel with engineering, procurement, and construction

[TO BE COMPLETED: Detailed Gantt chart to be prepared using the Portal Reference Documents template or equivalent, and attached as annex to Part B.]
