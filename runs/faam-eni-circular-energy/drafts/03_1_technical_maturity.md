# 3.1 Technical Maturity

## 3.1a Technical Maturity -- Overview

The FAAM-ENI Circular Energy project integrates two proven technology domains -- solid-state LFP cathode active material (CAM) synthesis and ISO 23247-compliant digital twin manufacturing -- into a first-of-kind electrified production facility at Brindisi, Italy. The core technology readiness levels are summarised below, with detailed TRL justifications provided in Section 1 (Degree of Innovation) and in the mandatory Feasibility Study annex.

| Technology Component | Current TRL | Target TRL at EiO | Basis |
|---|---|---|---|
| Solid-state LFP synthesis (spray dry + calcine) | TRL 7-8 | TRL 9 | Dominant industrial route globally; proven at >10,000 t/yr scale in China [CLM-001, SRC-011] |
| Electrified spray drying (electric resistance heaters) | TRL 7 | TRL 9 | Commercially available equipment (e.g., GEA, Buchi industrial); proven in ceramics and food at equivalent temperatures [SRC-ED-001] |
| Electrified calcination (electric roller hearth kiln / rotary kiln) | TRL 7 | TRL 9 | Electric roller hearth kilns commercially available from NGK, Kanthal/Sandvik up to 1500 C; deployed for NMC CAM production [SRC-ED-009, SRC-ED-010, SRC-ED-023] |
| ISO 23247 digital twin framework | TRL 5-6 | TRL 7-8 | Validated in discrete manufacturing (NIST, automotive); not yet applied to thermal/chemical powder synthesis [CLM-008, SRC-007] |
| Multi-scale process models (CFD, PBM, DEM) | TRL 4-5 | TRL 6-7 | Individual models validated in analogous processes; integration into unified DT is the novel step [CLM-018, SRC-DT-REPORT] |
| PAT/QbD sensor integration | TRL 5-6 | TRL 7-8 | Sensors commercially proven; pharmaceutical PAT framework transferable but not yet demonstrated for CAM [CLM-013, SRC-028] |

The core manufacturing process (solid-state LFP synthesis via spray drying and calcination) is at industrial maturity, with the electrification of process heat being the primary technical advancement. The digital twin components represent the higher-risk, higher-innovation elements of the project, but are built upon validated sub-systems and established standards.

**Co-located JV factory as technical de-risking mechanism.** The LFP CAM plant is co-located with a planned FIB-Eni joint venture battery cell and BESS manufacturing facility at the same Brindisi site. This co-location creates an immediate feedback loop from cell manufacturing to CAM quality: cell performance data from the JV factory feeds directly into the DT's quality prediction models, enabling rapid identification of CAM quality parameters that impact downstream cell performance. This closed-loop quality feedback cycle — from CAM synthesis through cell testing and back to process optimisation — is a unique technical advantage unavailable to standalone CAM producers selling to external customers. The co-located JV factory also secures internal offtake, eliminating market risk for the CAM product and ensuring continuous production data for DT model calibration.

Detailed technical feasibility is described below and supported by the Feasibility Study annex.

**Reference**: Full feasibility study attached as mandatory annex (max 60 pages), covering process flow diagrams, schematic layouts, mass and energy balances, and technical risk analysis.

## 3.1b Technical Feasibility

### LFP CAM Production Process

The Brindisi plant employs a wet-route solid-state synthesis process comprising seven sequential unit operations, designed to produce battery-grade LiFePO4 cathode active material. The process is described below with reference to the block flow diagrams in the Feasibility Study annex.

**Step 1: Raw Material Dosing and Dispersion**

The three primary precursors -- iron phosphate (FePO4), lithium carbonate (Li2CO3), and glucose (C6H12O6, carbon source) -- are gravimetrically dosed into a stirred dispersion tank with deionised water. The stoichiometric ratio targets Li:Fe:P = 1.00:1.00:1.00 (molar), with lithium carbonate providing a slight excess (typically 2-5 mol% Li excess) to compensate for volatilisation losses during calcination [SRC-011]. The glucose loading is 5-15 wt% relative to the total solid content, providing the carbon precursor for in-situ carbon coating during calcination [CLM-020, SRC-DT-REPORT]. The resulting aqueous slurry (typically 30-45 wt% solids) is homogenised by high-shear mixing.

**Step 2: Sand Milling and Magnetic Particle Removal**

The homogeneous slurry is transferred to a horizontal sand mill (bead mill) for particle size reduction and intimate mixing of the precursors. The target particle size after milling is D50 < 5 um, verified by at-line laser diffraction measurement. Following milling, the slurry passes through an electromagnetic demagnetiser to remove ferromagnetic contaminants introduced during milling (iron wear particles from the mill media). Magnetic contamination above 0.1 ppm Fe metallic is a critical defect that can cause internal short circuits in the final battery cell [SRC-DT-REPORT].

**Step 3: Spray Drying (ELECTRIFIED)**

The milled aqueous slurry is fed to an industrial co-current spray dryer equipped with a rotary atomiser or pressure nozzle system. The spray dryer inlet air is heated to 200-250 C using electric resistance heaters, replacing the conventional natural gas burners used in Asian benchmark facilities [CLM-011, SRC-ED-001]. The outlet air temperature is controlled at 90-120 C. Spray drying transforms the aqueous slurry into a dry, free-flowing solid precursor powder with engineered particle morphology -- spherical secondary particles comprising intimately mixed primary precursors with uniform glucose distribution.

The spray dryer is a critical quality-determining step: inlet temperature, feed rate, atomiser speed, and air flow rate directly control the dried particle size (D50), morphology (sphericity), residual moisture (<2 wt%), and spatial homogeneity of the carbon precursor within the granule [CLM-009, SRC-012, SRC-013]. Electrification of the spray dryer provides superior temperature control precision compared to gas-fired heating (resistance heaters achieve +/-1 C vs. +/-5-10 C for gas burners), which is advantageous for batch-to-batch consistency [SRC-ED-018].

Electric resistance heating elements (Kanthal Tubothal or SiC elements, rated to 1100 C) are commercially proven in industrial spray dryers for ceramics and food processing at comparable throughputs [SRC-ED-009]. The specific thermal energy demand for spray drying of aqueous slurries is approximately 0.70-1.10 kWh per kg of water evaporated, based on data from the Italian ceramics industry operating in the same geographic region [SRC-ED-021].

The plant comprises 4 modular production lines, each rated at 12,500 t/yr, for a total nameplate capacity of 50,000 t/yr (50 kton/yr). Each line includes its own spray dryer train sized to support the line's throughput requirements. The workshop footprint is approximately 161.1 m x 106 m (~17,100 m2).

**Step 4: Calcination (ELECTRIFIED -- Key Innovation Step)**

The dried precursor powder is loaded into saggars and introduced into the calcination furnace (roller hearth kiln or pusher kiln configuration) via an automated rail/conveyor system. The furnace operates under nitrogen atmosphere (pO2 < 10 ppm) at 650-700 C for 6-12 hours [CLM-020, SRC-011]. Nitrogen consumption is approximately 850 m3 per tonne of LFP CAM product.

Two electrified furnace configurations are under evaluation for the Brindisi plant:

- **Electric roller hearth kiln (RHK)**: The industrial standard for battery cathode active material calcination. Electric heating zones with independent PID control provide uniform temperature distribution across the kiln cross-section. The NGK HD series and equivalent kilns operate to 1500 C with 40%+ energy reduction versus conventional tunnel kilns [SRC-ED-023]. A CFD-validated model for electric RHK energy optimisation in NMC CAM calcination has been published (Jo et al., 2025), demonstrating <5% heater control deviation [SRC-ED-010]. This model is directly transferable to LFP calcination at the lower operating temperature of 650-700 C.

- **Electric rotary kiln**: An alternative for continuous throughput. Electric internally-heated or externally-heated rotary calciners have been demonstrated for cement and lime production [SRC-ED-006, SRC-ED-007, SRC-ED-008]. Kanthal (Sandvik Group) supplies electric heating elements (SiC, Tubothal, Fibrothal) rated to 1100 C for battery cathode kiln applications [SRC-ED-009].

Electric kilns achieve 95% thermal efficiency compared to 25% (gas without heat recovery) to 60% (gas with best-in-class heat recovery), representing a 1.6-3.8x thermal efficiency advantage [CLM-023, SRC-ED-009]. For the same thermal work, an electric kiln uses 37-63% of the fuel energy input of a gas-fired kiln. This efficiency gain reduces both operating cost and GHG emissions per tonne of LFP CAM produced.

During calcination, the following sequential reactions occur with activation energies ranging from 65-180 kJ/mol [CLM-020, SRC-DT-REPORT]:
1. Dehydration and organic decomposition (200-400 C): glucose pyrolysis generates amorphous carbon
2. Carbothermal reduction of Fe3+ to Fe2+ (400-550 C): carbon reduces iron phosphate
3. Olivine crystallisation (550-700 C): nucleation and growth of the LiFePO4 phase (Jander/Avrami kinetics)
4. Carbon coating consolidation (600-700 C): residual carbon forms a 2-5 nm conductive layer on LFP particles

Precise temperature profile control across these stages is the primary determinant of product quality. The nitrogen atmosphere must be maintained at pO2 < 10 ppm to prevent Fe2+ oxidation to Fe3+, which degrades electrochemical performance [SRC-DT-REPORT].

**Step 5: Jet Milling**

The calcined product is de-agglomerated by jet milling (air-flow grinding). The jet mill uses compressed nitrogen or air to achieve high-velocity interparticle collisions, breaking agglomerates while preserving the olivine crystal structure and carbon coating integrity. The target D50 after jet milling is 0.7-2.5 um.

**Step 6: Classification and Demagnetisation**

The milled powder passes through an ultrasonic vibrating sieve (typical cut-off 10-20 um) to remove oversized particles, followed by an electromagnetic dry powder separator for removal of any ferromagnetic contaminants introduced during milling. The final D50, span (D90-D10)/D50, and magnetic contamination level are verified by at-line laser diffraction and magnetic susceptibility measurement, respectively.

**Step 7: Automated Packaging**

Qualified LiFePO4 product is automatically packaged under inert atmosphere (N2 blanketing) in moisture-barrier bags to maintain battery-grade moisture levels (<750 ppm). Each batch is assigned a unique lot number with full traceability to all process parameters and quality data.

### Mass and Energy Balance

**Mass balance (per tonne of LFP CAM product, from production document)**:

| Input | Quantity per tonne LFP CAM | Annual at 50 kton/yr |
|-------|---------------------------|---------------------|
| Iron phosphate (FePO4) | 0.98 t | 49,000 t |
| Lithium carbonate (Li2CO3) | 0.25 t | 12,500 t |
| Glucose (C6H12O6) | 0.010 t | 500 t |
| TiO2 | 0.008 t | 400 t |
| H3PO4 | 0.006 t | 300 t |

The stoichiometric yield is >95% for the lithium and iron-phosphorus streams; the primary mass loss is CO2 from carbonate decomposition and volatiles from glucose pyrolysis. Water is evaporated during spray drying and recovered; nitrogen carrier gas is recycled after scrubbing.

**Energy and utility balance (per tonne of LFP CAM product, from production document)**:

| Utility | Quantity per tonne LFP CAM |
|---------|---------------------------|
| Electricity | 3,580 kWh |
| Production water | 4 t |
| Pure water | 5 t |
| Natural gas | 189 m3 |
| Nitrogen | 850 m3 |

The two energy-intensive steps are spray drying and calcination, which together account for >80% of total process energy consumption [CLM-024, SRC-ED-014]. The measured electricity consumption of 3,580 kWh/t is consistent with the estimated range of 3-6 kWh/kg from NMC CAM analog data (Ahmed et al., 2017 [SRC-ED-011]). The natural gas consumption of 189 m3/t reflects the initial plant configuration; the progressive electrification strategy aims to reduce and eventually eliminate this gas use through electric alternatives in spray drying and calcination auxiliary heating.

**Production capacity**: The plant is designed for an annual nameplate capacity of **50,000 tonnes (50 kton/yr)** of battery-grade LFP CAM, organised across 4 modular production lines of 12,500 t/yr each. This exceeds the comparable FREYR project (30,000 t/yr [SRC-025]) and positions the Brindisi facility as the largest planned LFP CAM plant in Europe. The target market is primarily ESS cell manufacturers.

### Critical Quality Attributes (CQAs)

The following CQA targets define battery-grade LFP CAM, per the QbD framework developed in the DT deep-dive report [SRC-DT-REPORT, CLM-009]:

| CQA | Target | Specification | Measurement Method |
|---|---|---|---|
| D10 particle size | 0.3-1.0 um | Range | Laser diffraction |
| D50 particle size | 0.7-2.5 um | Range | Laser diffraction |
| D90 particle size | 2.5-12.0 um | Range | Laser diffraction |
| Specific surface area (SSA) | 10-14 m2/g | Range | N2 adsorption (BET) |
| Tap density | 1.0-1.4 g/cm3 | >1.0 g/cm3 | ASTM B527 |
| Pellet density | >=2.40 g/cm3 | Min 2.40 g/cm3 | Compaction measurement |
| Electrode press density | >=2.30 g/cm3 | Min 2.30 g/cm3 | Press density measurement |
| Phase purity (olivine) | >98% | Min 97% | XRD Rietveld refinement |
| Carbon content | 1.0-1.8 wt% | Range | TGA / combustion analysis |
| Fe2+/Fe3+ ratio | >0.95 | Min 0.90 | Mossbauer / XPS |
| Discharge capacity (0.1C) | >=155 mAh/g | Min 150 mAh/g | Half-cell electrochemical testing |
| Discharge capacity (1C) | >=140 mAh/g | Min 135 mAh/g | Half-cell electrochemical testing |
| Initial Coulombic Efficiency | ~98% | Min 96% | Half-cell electrochemical testing |
| Moisture | <750 ppm | Max 750 ppm | Karl Fischer titration |
| Magnetic impurities | <=1000 ppb | Max 1000 ppb | Magnetic susceptibility |

### Digital Twin Architecture

The digital twin is designed according to ISO 23247:2021, the international standard for manufacturing digital twins [CLM-008, SRC-007, SRC-008]. The four-layer architecture maps directly to the Brindisi plant equipment and control systems:

**Layer 1 -- Observable Manufacturing Element (OME)**: The physical plant assets, including the spray dryer, calcination furnace (RHK or rotary kiln), jet mill, classifier, and all QC instrumentation. Each major equipment unit is assigned a unique asset identifier and a digital representation within the twin.

**Layer 2 -- Data Collection and Device Control (DCDC)**: The sensor network and industrial communication layer. Sensors include:
- Temperature: Type K/S thermocouples (contact measurement, +/-1.5 C accuracy) and ratio pyrometers (non-contact, +/-0.5%) for furnace zone monitoring; IR cameras for full-field 2D thermal mapping of crucible beds
- Particle size: FBRM (Focused Beam Reflectance Measurement) probes for in-line monitoring during milling (0.5-2000 um, 2-second update rate); laser diffraction for at-line D10/D50/D90 verification
- Chemical composition: In-line Raman spectroscopy probes simultaneously measuring olivine phase formation (PO4 stretch at 950 cm-1), carbon coating quality (D/G band ratio), and impurity phases [CLM-019, SRC-DT-REPORT]
- Atmosphere: Zirconia O2 sensors (<10 ppm resolution), NDIR analysers for CO2/CO/CH4, QMS for evolved gas analysis during calcination

All sensor data is communicated via OPC-UA gateways to an edge-fog computing layer, with MQTT publish-subscribe messaging for real-time data streaming. Typical edge-to-fog latency is <100 ms [SRC-DT-REPORT].

**Layer 3 -- Digital Twin Core Entity**: The computational engine comprising:
- Physics-based models: CFD for furnace temperature distribution (COMSOL/OpenFOAM), population balance models (PBM) for particle size evolution during milling, DEM for milling media dynamics, and multi-step Jander/Avrami reaction kinetics for calcination [CLM-018, SRC-DT-REPORT]
- Physics-informed neural networks (PINNs): Reduced-order surrogate models trained on CFD/PBM simulation data, enabling real-time prediction with <1 second latency [SRC-DT-REPORT]
- ML pipelines: Anomaly detection (autoencoder-based, following the Fraunhofer DiBaZ approach [CLM-017]), multivariate SPC, and predictive quality models correlating CPPs to CQAs
- Time-series database: InfluxDB for high-frequency sensor data storage; HDF5/Delta Lake for batch archival and retrospective analysis

**Layer 4 -- User Entity**: The human-machine interface comprising:
- Grafana real-time dashboards displaying process state, CQA predictions, and control actions
- Model Predictive Control (MPC) operator interface for furnace temperature profile optimisation, milling parameter adjustment, and spray dryer tuning
- Batch quality reports with automatic pass/fail disposition against CQA specifications
- Decision support: recommended parameter adjustments for next batch based on current batch outcomes

### Technology Licensor

FIB has secured a technology licensor for the LFP CAM solid-state synthesis process — [TO BE COMPLETED: technology licensor name] — which provides a critical risk mitigation pathway for scale-up. The technology licensor contributes: (a) proven process recipes and calcination profiles validated at industrial scale; (b) equipment specification guidance for the roller hearth kiln, spray dryer, and milling systems; and (c) commissioning support including process parameter transfer and initial batch qualification protocols. This licensor relationship substantially de-risks R1 (calcination scale-up) and TR5 (product quality consistency) by providing an established process baseline from which the DT-driven optimisation can begin.

### DT Development Milestones

The digital twin development follows a structured timeline integrated with the plant construction and commissioning schedule:

| Milestone | Month | TRL Target | Deliverable |
|-----------|-------|------------|-------------|
| DT architecture specification | M6 | — | ISO 23247 architecture document |
| Sensor specification + procurement | M9 | — | PAT sensor procurement contracts |
| Calcination CFD model validated | M12 | TRL 4 | Model validated on vendor test data |
| PBM for spray drying validated | M15 | TRL 4 | Particle size prediction within +/-10% |
| Surrogate model library built | M18 | TRL 5 | ROM/PINN models for real-time use |
| Edge computing infrastructure | M18 | — | Edge gateways deployed |
| Layer 2 (DCDC) operational | M24 | — | All sensors streaming to DT platform |
| MPC for calcination demonstrated | M30 | TRL 5 | Closed-loop temperature control |
| Layer 3 (Core DT) operational | M36 | TRL 6 | Full model chain operational |
| QbD/PAT framework validated | M40 | TRL 6 | CQA prediction within spec |
| Full ISO 23247 Layer 4 integration | M42 | TRL 6 | Dashboard + MPC + quality reports |
| DT validated on production batches | M48 | TRL 6-7 | First production data feedback loop |
| DT optimisation (Year 1-2 operation) | M60 | TRL 7 | Model calibration with real data |

### Technical Risks and Mitigation (Summary)

The principal technical risks are described in detail in Section 3.4 (Risk Management). In brief:

- **Scaling multi-scale models to real-time**: The full CFD + PBM + reaction kinetics chain requires hours of computation for a single calcination cycle. Mitigation: surrogate models (PINNs, neural network emulators) trained on offline simulations provide real-time predictions within <1 second, validated against offline models at commissioning [CLM-016, SRC-DT-REPORT].
- **Sensor reliability at >600 C**: Raman probes require sapphire windows that may foul at calcination temperatures; FBRM cannot survive >600 C. Mitigation: redundant sensing architecture combining contact sensors (thermocouples) with non-contact sensors (pyrometers, IR cameras); at-line measurement protocols for CQAs that cannot be monitored truly in-line during calcination; virtual sensors (ML-inferred CQA predictions) as backup when physical sensors are offline [CLM-019].
- **DT-process coupling latency**: Closed-loop MPC requires sensor-to-actuator response within the process time constant. Mitigation: edge computing for time-critical control loops (furnace zone temperature); fog layer for batch-level optimisation; cloud for retrospective analysis and model retraining. The edge-fog-cloud architecture ensures appropriate latency for each control tier [SRC-DT-REPORT].

## 3.1c Due Diligence Reports

[TO BE COMPLETED: Independent technical due diligence reports to be referenced here if available (e.g., from equipment vendor assessments, independent process review). The Feasibility Study annex serves as the primary technical documentation for this proposal. The production information document provides detailed process and equipment specifications supporting the technical feasibility assessment.]
