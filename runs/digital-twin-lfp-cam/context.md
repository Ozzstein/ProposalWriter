# Project Context: Digital Twin for LFP CAM Manufacturing

## Project Identity
- **Project name**: digital-twin-lfp-cam
- **Full title**: Digital Twin Framework for LFP Active Material Powder Manufacturing
- **Created**: 2026-04-01
- **Target deadline**: Mid April 2026 (~2 weeks) — **Stage 1 Concept Note**
- **Application stage**: Stage 1 (Concept Note, ~25 pages)

## Funding
- **Agency**: European Commission — Innovation Fund
- **Instrument**: Innovation Fund large-scale (grant >€7.5M)
- **Stage**: Stage 1 — Concept Note

## Research Topic
A four-layer ISO 23247-compliant digital twin (DT) for the manufacturing of next-generation LFP (Lithium Iron Phosphate) cathode active material (CAM) powder, enabling:
- **Live Quality Control**: real-time monitoring of CQAs (D50, phase purity, Fe²⁺/Fe³⁺ ratio, carbon content) via PAT sensors (Raman, FBRM, pyrometry, XRD)
- **Fine-tuning**: closed-loop MPC of calcination furnaces and adaptive milling control
- **Material evolution tracking**: batch-to-batch Bayesian updating of physics-based models (CFD, PBM, DEM)

## Core Innovation — The Gap This Fills
**As of 2026, no published integrated DT exists for LFP CAM powder synthesis from precursors.**
- ARTISTIC (Franco et al., CNRS): covers electrode manufacturing — downstream of CAM
- DiBaZ (Fraunhofer ITWM): covers cell production — also downstream
- TwinHeat (MINES Paris): covers generic industrial furnaces, not LFP-specific chemistry
- **This project fills the upstream gap**: from raw precursors → battery-grade LFP powder

This is explicitly documented as a research gap in the technical report (Section 10.1).

## Key Hypothesis
A physics-based, multi-scale digital twin integrating CALPHAD thermodynamics, CFD furnace models, Population Balance Models (PBM), and Discrete Element Method (DEM) milling models — continuously updated by real-time PAT sensor data — can:
1. Reduce scrap rates by >10% (from ~5% to <4.5%)
2. Reduce calcination energy consumption by 12–15%
3. Reduce batch-to-batch variability in CQAs by >40%
4. Enable Real-Time Release Testing (RTRT) for EU Battery Regulation compliance

## Quantitative KPIs (from cross-industry DT benchmarks in report)
| KPI | Target | Evidence Base |
|---|---|---|
| Scrap rate reduction | >10% | Fraunhofer FFB: 10.3%; Barua et al.: 49% defect reduction |
| Energy reduction | 12–15% | TwinHeat: 10-15%; BASF: 5-8% per reactor |
| Batch-to-batch variability | >40% reduction | Report executive summary |
| Time-to-specification | 30–50% reduction | Cross-industry benchmark |
| Out-of-spec batches | >50% reduction | GSK pharmaceutical case study |

## DT Architecture (Four-Layer ISO 23247)
1. **Physical/Sensing Layer**: Rotary kiln, ball/jet mill, autoclave, classifiers + sensors (thermocouples, pyrometers, FBRM, Raman probes, O₂/CO₂ analyzers, laser diffraction, XRF)
2. **Data/Communication Layer**: OPC-UA, MQTT, InfluxDB (time-series), Delta Lake, Apache Kafka
3. **Model/Analytics Layer**: CFD (COMSOL/OpenFOAM), PBM, DEM, PINNs surrogates, MPC controller, Bayesian optimizer, PLS/PCA multivariate SPC
4. **Application/Decision Layer**: Grafana dashboards, MPC operator interface, RTRT quality release, EU Battery Passport data export

## Critical Quality Attributes (CQAs) Monitored
- D₅₀: 1–3 µm (±0.5 µm) — rate capability, packing density
- Span (D₉₀–D₁₀)/D₅₀: <2.0 — electrode homogeneity
- BET surface area: 12–18 m²/g — electrolyte wetting
- Phase purity: >98% olivine (XRD Rietveld) — capacity, cycle life
- Fe²⁺/Fe³⁺ ratio: >0.95 — electronic conductivity
- Carbon content: 1.5–3.0 wt% (D/G ratio 0.8–1.2) — conductivity vs. gravimetric capacity
- Discharge capacity: >155 mAh/g (C/10) — final product specification
- Moisture: <200 ppm — gas generation, cycle life

## EU Policy Alignment
- **EU Battery Regulation (2023/1542)**: requires digital product passport for all batteries by 2027 — this DT is the natural data backbone for passport compliance (traceable process-to-performance linkages per batch)
- **Critical Raw Materials Act**: LFP uses no Co/Ni — strategically important for EU supply chain resilience
- **Net Zero Industry Act**: battery manufacturing is a strategic technology
- **Industry decarbonisation**: calcination at 600–750°C is energy-intensive; DT-enabled 12–15% energy reduction = direct GHG reduction

## Carbon Abatement Case (for Innovation Fund)
The Innovation Fund carbon abatement case rests on:
1. **Direct energy reduction**: 12–15% reduction in calcination energy (electricity/gas for rotary kiln operation)
2. **Scrap reduction**: >10% less wasted LFP powder = less embodied energy and raw material loss
3. **Upstream decarbonisation enabler**: higher-quality, more consistent LFP CAM → more reliable batteries → accelerated electrification of transport
4. **EU Battery Passport compliance**: DT provides the data infrastructure for the mandatory digital product passport by 2027

*Note: Quantitative carbon abatement numbers (tCO₂eq/year) require FAAM's production capacity and energy consumption data — to be obtained.*

## Team
- **Lead applicant**: FAAM (joint venture of FIB S.p.A. and Eni)
  - FIB S.p.A.: Italian industrial battery manufacturer
  - Eni: Italian energy major (strategic partner for energy transition)
- **Partners**: TBD — research institutions, technology providers

## Key References from Research Report
- Franco et al., ECS 2023 & 2025 (ARTISTIC platform)
- Thelen et al., arXiv 2022 (comprehensive DT review, parts 1 & 2)
- Rostami et al., ChemPhysChem 2024 (LFP thermodynamics)
- Grageda et al., Nanomaterials 2023 (sol-gel LFP, 163 mAh/g)
- Fraunhofer ITWM, DiBaZ press release 2024 (battery production DT)
- MINES Paris, TwinHeat 2024 (furnace DT, 10-15% energy reduction)
- ISO 23247:2021 (digital twin manufacturing framework)
- EU Battery Regulation 2023/1542 (digital product passport)
- Raissi et al., J. Computational Physics 2019 (PINNs)
- Kalidindi et al., Frontiers in Materials 2022 (PSP linkages)

## Open Questions (to resolve before /parse-call)
1. What specific Innovation Fund call/topic is being targeted? (IF 2025 Large Scale?)
2. What is FAAM's current LFP production capacity (tonnes/year)?
3. What synthesis route does FAAM use? (solid-state is industrial standard)
4. What is current energy consumption per tonne of LFP produced?
5. What is the current TRL of the DT components? (report suggests TRL 4-5 for individual models)
6. Are there additional consortium partners (research institutes, technology providers)?
