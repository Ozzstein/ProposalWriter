# Section 1: Degree of Innovation

**Scoring: 15 pts x 2 weight = 30 weighted pts | Minimum pass: 9/15 | CASCADE GATE**

## 1.1 Innovation in Relation to the State of the Art

### Commercial State-of-the-Art

Global LFP cathode active material production is dominated by Chinese manufacturers. CATL, BYD, Gotion High-Tech, and Dynanonic collectively control over 99% of global capacity [CLM-001], with all commercial-scale plants located in China [SRC-022, SRC-023]. No European manufacturer operates a commercial LFP CAM production line [CLM-003].

The commercial production process at incumbent Chinese facilities follows a well-established pattern:

- **Thermal processing**: Natural gas-fired rotary kilns for calcination at 600-700 C and gas-heated spray dryers for precursor drying. Gas-fired kilns achieve 25-60% thermal efficiency depending on heat recovery configuration [CLM-023, SRC-ED-009]. Gas combustion introduces combustion products into the kiln atmosphere, complicating the strict pO2 control (<10 ppm under N2) required for phase-pure olivine formation.

- **Process control**: Recipe-based, empirical approaches. Calcination temperature profiles, dwell times, and atmosphere conditions are fixed based on historical production experience. Process adjustment occurs between batches based on offline quality testing of finished product, not during production. Wang et al. (2023, 50 citations) explicitly identified the gap in theoretical models and in-line monitoring for industrial cathode precursor synthesis [SRC-028, CLM-013].

- **Quality assurance**: Offline batch testing after production completion. Critical quality attributes (D50, BET, phase purity, carbon content, discharge capacity) are measured at-line or off-line using XRD, BET analysis, particle size analysis, and electrochemical testing. There is no real-time, in-process quality prediction capability in current commercial LFP CAM production.

- **Digital integration**: No published evidence of integrated digital twin technology deployed in any commercial LFP CAM production facility. Chinese producers may have unpublished proprietary systems, but systematic searches across two independent review papers (Ayerbe et al., 2021 [SRC-001]; Dubarry et al., 2023 [SRC-002]), the patent landscape (12 patents analysed including CNIPA), and a 35-page deep-dive technical report [SRC-DT-REPORT] confirm this gap. The ARTISTIC group (U. Picardie Jules Verne) explicitly scoped their work to electrode manufacturing, not CAM synthesis [SRC-004, CLM-006].

**Innovation Fund portfolio context**: FREYR Battery received EUR 122M (October 2024) for a 30,000 t/yr LFP CAM facility in Vaasa, Finland [SRC-025]. However, FREYR has not specified progressive electrification of process heat, has not reached FID for Vaasa, and is currently prioritising its US Giga America facility [CLM-029]. The FAAM-ENI project differentiates on three axes: (i) progressively electrified process heat (66.6% electrification at entry into operation, with a roadmap to >95%); (ii) integrated ISO 23247 digital twin; and (iii) a more advanced project maturity trajectory with a committed brownfield site and co-investor (Eni).

### Technological State-of-the-Art

The technological frontier relevant to this project spans three domains: digital twins for battery manufacturing, electrification of industrial process heat, and process analytical technology for powder manufacturing.

#### Digital Twins in Battery Manufacturing

Three principal DT implementations define the technological state-of-the-art:

**ARTISTIC Platform** (Franco group, Universite de Picardie Jules Verne; ERC-funded) [SRC-003, SRC-004]: The most comprehensive DT for battery electrode manufacturing. Employs a multi-scale simulation chain: coarse-grained molecular dynamics for slurry preparation, lattice models for coating/drying, discrete element method (DEM) for calendering, lattice Boltzmann method (LBM) for electrolyte filling, and finite element method (FEM, Newman P2D) for electrochemical performance. Validated for NMC111, NMC622, LFP, graphite, and silicon-graphite electrodes. Key achievement: Bayesian optimisation-driven inverse design finds optimal manufacturing parameters in fewer than 50 iterations (Duquesnoy et al., 2022, 81 citations in Energy Storage Materials [SRC-004]). **Critical limitation**: ARTISTIC addresses electrode-level manufacturing (slurry to cell), not upstream CAM powder synthesis from precursors [CLM-006].

**TwinHeat** (MINES Paris industrial chair) [SRC-DT-REPORT]: Industrial DTs for heat treatment optimisation of furnaces. Uses a dual AI loop: (1) CFD-generated training data combined with neural network surrogates for real-time temperature prediction, and (2) deep reinforcement learning for energy-optimal furnace control. Has demonstrated 10-15% energy reduction and <1 C prediction accuracy on carburising, nitriding, and quenching furnaces [CLM-016]. The approach is directly transferable to calcination furnace DT, substituting carburising chemistry with LFP reaction kinetics. **Critical limitation**: Applied to metallurgical heat treatment, not battery CAM synthesis.

**Fraunhofer ITWM DiBaZ** [SRC-DT-REPORT]: DT covering all process steps in battery cell production, from electrode coating through formation. Includes inline CT quality control, physics-based drying/calendering/filling models, and autoencoder-based anomaly detection. Fraunhofer FFB has reported a 10.3% scrap rate reduction using DT-guided process optimisation [CLM-017]. **Critical limitation**: Covers cell-level production, not CAM powder synthesis.

**Li et al. (2024)** [SRC-006]: DT for LFP battery pack assembly line optimisation — 3D digital representation enabling production flow simulation. Addresses pack assembly only.

**Ma et al. (2023)** [SRC-014]: Predictive model for NMC811 sintering furnace integrating chemical reactions, thermal conduction, and CFD. Validated with <10% error. Represents a physics-based process model applicable to calcination but was not implemented as an integrated DT.

**The gap**: No published or patented digital twin exists for upstream CAM powder production from precursors [CLM-005]. The spray drying to calcination to milling chain — where final CAM quality is determined — has no DT coverage in the literature. This gap is confirmed by two independent review papers (Ayerbe et al., 2021, 124 citations [SRC-001]; Dubarry et al., 2023, 38 citations in Joule [SRC-002]) and the comprehensive deep-dive report [SRC-DT-REPORT].

#### ISO 23247 Digital Manufacturing Framework

ISO 23247 (2021) defines the reference architecture for manufacturing DTs through a four-layer functional model [SRC-007, SRC-008]. Published implementations include:

- Shao (2021, NIST): Three use cases on the NIST Smart Manufacturing Systems Test Bed for CNC machining — the definitive ISO 23247 reference (43 citations) [SRC-007]
- Cabral et al. (2023): ISO 23247-compliant DT for CNC milling centre using MQTT and MTConnect [SRC-009]
- Melo et al. (2024): ISO 23247-compliant DT for automotive body shop inspection enabling zero defect manufacturing [SRC-010]

**All published ISO 23247 implementations are in discrete manufacturing** (machining, assembly) or additive manufacturing. No peer-reviewed implementation exists for thermal/chemical powder synthesis processes [CLM-008]. Applying ISO 23247 to continuous/batch chemical manufacturing where the standard must accommodate reaction kinetics feedback, atmosphere control, and multi-phase transformations is an undemonstrated extension.

#### Electrification of Industrial Process Heat

Industrial process heating accounts for approximately 20% of global CO2 emissions [CLM-010, SRC-018]. Electrification technologies for high-temperature heat (>400 C) are technically proven [SRC-016, SRC-017]:

- Electric resistance heating: mature at TRL 7-9 for kilns, achieving 95% thermal efficiency versus 25-60% for gas [CLM-023, SRC-ED-009]
- Electric roller hearth kilns: the established industrial standard for NMC CAM calcination, with validated CFD models (Jo et al., 2025 [SRC-ED-010]) and commercial equipment (NGK [SRC-ED-023])
- High-temperature heat pumps (HTHP): demonstrated at COP 3.04-3.6 for spray dryer pre-heating [SRC-ED-004, SRC-ED-005]

Electrified calcination has been demonstrated in cement (Liu et al., 2023 [SRC-019]) and lime (Dylong et al., 2025 [SRC-020]). Kanthal (Sandvik Group) documents 95% thermal efficiency for electric kilns versus 25-60% for gas kilns in battery material applications [SRC-ED-009].

**The gap**: No published work validates progressively electrified process heat (spray drying + calcination) specifically for LFP CAM synthesis at production scale [GAP-003]. Electric roller hearth kilns exist; HTHP-assisted spray drying exists; the specific combination applied to LFP CAM with its strict atmosphere (pO2 <10 ppm), temperature profile (600-700 C), and product quality requirements (phase-pure olivine) has not been demonstrated.

---

### Innovation Beyond the State-of-the-Art

The FAAM-ENI project delivers innovation across four pillars, each addressing a documented gap in the current state-of-the-art. The innovation is not incremental: it creates capabilities that do not currently exist at any scale, combining technologies that have been proven independently but never integrated for LFP CAM manufacturing.

#### Innovation Pillar 1: First Digital Twin for LFP CAM Powder Synthesis [NOV-001]
*Defensibility score: 8/10 — highest novelty anchor*

**What is new**: An integrated digital twin spanning the full LFP CAM production chain — from spray drying through calcination to jet milling — providing real-time quality prediction and closed-loop process control. This fills the documented gap between electrode-level DTs (ARTISTIC [SRC-004]) and cell-level DTs (DiBaZ [SRC-DT-REPORT]).

**Multi-scale modelling framework**: The DT core entity implements a physics-based modelling hierarchy that bridges six length scales:

| Scale | Method | Application in LFP DT | Key outputs |
|-------|--------|----------------------|-------------|
| Atomistic | DFT (VASP/Quantum ESPRESSO) | LFP olivine formation energetics, defect energies, Li+ migration barriers | Thermodynamic parameters, diffusion coefficients |
| Molecular | Molecular dynamics | Carbon coating pyrolysis mechanisms, surface adsorption | Carbon coating quality parameters |
| Mesoscale | Phase-field / kinetic Monte Carlo | Nucleation and grain growth kinetics during calcination | Grain size distribution, phase evolution |
| Continuum | CFD + PBM + reaction kinetics | Calcination kiln heat/mass transfer; spray dryer droplet drying; Jander/Avrami reaction kinetics | Temperature profiles, conversion rates, particle size evolution |
| Equipment | DEM for jet milling | Particle breakage and classification | Milled particle size distribution (D50, D90) |
| Plant | Flowsheet simulation (Aspen Plus/gPROMS) | Mass/energy balance, throughput optimisation | Production rate, energy consumption, yield |

The multi-scale chain does not run in real-time at all scales simultaneously. DFT and mesoscale calculations are performed offline to generate material property databases and calibration parameters. These feed into continuum-scale surrogate models (neural network approximations of CFD and PBM solutions, trained on high-fidelity simulation datasets) that execute in real-time (<1 second inference) for closed-loop control [CLM-018]. This surrogate-based hierarchy is the approach validated by TwinHeat for furnace control (achieving <1 C prediction accuracy [CLM-016]) — here extended to chemical powder synthesis for the first time.

**Real-time ISO 23247 Layer 4 process twin**: The DT implements the ISO 23247 four-layer architecture mapped onto the 7-step LFP CAM production line [CLM-008]:

- **Layer 1 (OME)**: Physical production equipment instrumented with PAT sensors at each process step
- **Layer 2 (DCDC)**: OPC-UA/MQTT data exchange, edge computing nodes (latency <100 ms), PLC/SCADA integration
- **Layer 3 (Core DT)**: Physics-informed surrogate models for each unit operation; multi-fidelity uncertainty quantification; state estimation combining sensor data with model predictions via ensemble Kalman filtering
- **Layer 4 (User Entity)**: Model-predictive control (MPC) for calcination temperature profile, spray drying parameters, and milling energy; quality prediction dashboards; predictive maintenance

**Closed-loop MPC using physics-based + ML hybrid models**: The MPC controller operates on a receding-horizon optimisation that minimises a cost function combining product quality deviation (from CQA targets), energy consumption, and throughput. The controller receives real-time sensor data, updates state estimates through the physics-informed surrogate, and computes optimal setpoint trajectories for the next control horizon (5-15 minutes for calcination, 1-3 minutes for spray drying).

**PAT integration**: The DT ingests data from in-line and at-line sensors deployed across the production chain [CLM-019]:

| Sensor | Measurement | Location | Update rate |
|--------|------------|----------|-------------|
| Raman spectroscopy | Olivine phase (950 cm-1), carbon D/G ratio, impurities | Post-calcination (at-line) | 30-60 sec |
| FBRM (focused beam reflectance) | Chord length distribution | Milling, slurry | 2 sec |
| Laser diffraction | D10/D50/D90 | Post-milling (at-line) | 60 sec |
| Pyrometry (ratio pyrometer) | Temperature | Calcination kiln | 0.1 sec |
| IR camera | Temperature field (2D) | Kiln exit, spray dryer | 10 Hz |
| Zirconia O2 sensor | pO2 (<10 ppm) | Calcination kiln atmosphere | 1 sec |
| NDIR | CO2, CO, CH4 | Kiln exhaust | 1 sec |
| XRF | Elemental composition (Li, Fe, P) | Post-milling (at-line) | 5 min |

**Expected outcomes**: Based on cross-industry DT benchmarks validated across steel, chemicals, pharmaceuticals, and battery cell production [CLM-007]:
- Scrap rate reduction: 10-50% (Fraunhofer FFB demonstrated 10.3% in battery cell production [CLM-017])
- Energy consumption reduction: 12-15% (TwinHeat demonstrated 10-15% in furnace operations [CLM-016])
- Batch-to-batch variability reduction: >40%
- Unplanned downtime reduction: 20-50%

#### Innovation Pillar 2: Progressively Electrified LFP CAM Manufacturing [NOV-002]
*Defensibility score: 7/10*

**What is new**: The first LFP CAM production plant designed with a **progressive electrification strategy** — achieving a 66.6% electrification rate at entry into operation, with 3,580 kWh/t delivered electrically and 189 m3/t of natural gas (1,796 kWh_th/t, 33.4% of total process energy) retained for process steps where full electrification is not yet technically feasible at scale. Total process energy is 5,376 kWh/t. This achieves a significantly higher degree of electrification than the fully gas-fired Asian benchmark, and the plant architecture is designed to accommodate further gas-to-electric substitution as technology matures and Italy's grid decarbonises. The digital twin plays a central role in optimising the energy mix and identifying opportunities for progressive gas elimination.

**Electrification roadmap**:

| Phase | Electrification Rate | Gas Use (m3/t) | Key Change |
|-------|---------------------|----------------|------------|
| Entry into Operation (Y0) | 66.6% | 189 | Baseline design |
| Year 3 | ~75% | ~130 | HTHP for partial spray drying preheat |
| Year 5 | ~85% | ~80 | Extended HTHP coverage + electric kiln optimisation |
| Year 10 (target) | >95% | <25 | Full electric calcination, residual gas for backup only |

**Note on GHG scoring**: Per Section 1.3.4 of the Innovation Fund GHG emission avoidance methodology, the manufacturing plant producing components is outside the GHG calculation system boundary. The GHG avoidance for scoring purposes is calculated based on the use phase of the ESS systems in which the manufactured LFP CAM is deployed, not on the electrification of the manufacturing process itself. The progressive electrification of the plant is therefore an innovation and replicability strength (reducing the product carbon footprint and positioning the plant for long-term competitiveness), but it is not the basis of the GHG avoidance calculation under Section 2.

**Electrified calcination**: Electric roller hearth kiln (RHK) operating at 600-700 C under flowing N2 atmosphere, with calcination performed in saggars (consistent with roller hearth or pusher kiln configurations). The electric RHK achieves 95% thermal efficiency versus 25-60% for gas-fired rotary kilns [CLM-023, SRC-ED-009]. Electric heating provides superior temperature uniformity (critical for phase-pure olivine formation), eliminates combustion gas contamination of the inert atmosphere, and enables zone-by-zone temperature profile control compatible with DT-driven MPC optimisation. The electric RHK is the established industrial standard for NMC CAM calcination at temperatures to 950 C [SRC-ED-010, SRC-ED-023]; LFP calcination at 600-700 C is well within the proven operating envelope. The initial plant configuration retains some natural gas use (contributing to the 189 m3/t total gas consumption), particularly for auxiliary heating and drying stages where full electrification requires further technology maturation. The DT will optimise the balance between electric and gas heating to minimise both emissions and cost, while guiding the transition pathway toward full electrification.

**Heat pump-assisted spray drying**: High-temperature heat pump (HTHP) for spray dryer air pre-heating, achieving COP 3.04 at 120 C (Zuhlsdorf et al., 2017 [SRC-ED-004]) to COP 3.6 at 200 C (Zhao et al., 2024 [SRC-ED-005]). This means each kWh of electricity delivers 3.0-3.6 kWh of thermal heat for drying — a 2-3x thermodynamic advantage over direct electric resistance heating and a ~5-10x advantage over gas combustion when accounting for gas-fired dryer efficiency losses [SRC-ED-001]. Final drying stages use direct electric resistance or near-infrared (NIR) heating to reach the outlet temperatures required for complete solvent removal [SRC-ED-019].

**GHG and carbon footprint context**: The progressive electrification design is framed as a future-proof infrastructure investment. The 66.6% electrification rate achieved from day one is already substantially higher than the fully gas-fired Asian benchmark, and the plant architecture supports continued gas elimination over time. Note: per Section 1.3.4 of the Innovation Fund GHG methodology, the GHG avoidance for scoring purposes is calculated on the use phase of the manufactured battery components, not on the manufacturing plant itself. The electrification trajectory below therefore represents the plant's carbon footprint advantage — a key innovation and replicability differentiator — rather than the scored GHG avoidance metric:

| Year | Italy grid intensity (gCO2/kWh) | GHG reduction vs gas-fired benchmark | Basis |
|------|------|------|------|
| 2025 (current) | ~310 | Marginal (~5-15%) | ISPRA/Nowtricity [SRC-ED-016] |
| 2028 (breakeven) | ~180 | ~30-40% | NECP trajectory [SRC-ED-017] |
| 2030 (NECP target) | ~146 | 55-70% | Italy NECP, 65% renewables [CLM-026] |
| 2035 (G7 commitment) | ~30-60 | 80-90% | G7 2035 decarbonised power [CLM-026] |

The plant enters operation approximately 2028-2029, precisely when the Italian grid crosses the gas-breakeven threshold. Over the plant's 20+ year operational life, cumulative GHG avoidance accelerates as the grid continues to decarbonise [CLM-030]. Electrifying now avoids the capital cost of gas infrastructure that would become stranded assets within 5-7 years of installation.

**Electricity as the dominant GHG lever for LFP**: Lin et al. (2024) demonstrated that electricity consumption accounts for 39.7% of total global warming potential in LFP battery manufacturing — the single largest contributor [CLM-024, SRC-ED-015]. Switching to clean electricity is the most impactful single decarbonisation intervention, more effective than recycling or chemistry changes. Degen and Schutte (2021, 114 citations) showed that switching from gas+electricity to low-carbon electricity reduces battery cell GHG from 4.54 to 0.53 kgCO2eq/kWh — an 88% reduction [SRC-ED-013].

**NMC CAM energy analog**: No published LFP-specific industrial CAM synthesis energy data exists [CLM-028]. The best available analog is NMC CAM production at approximately 4 kWh/kg via co-precipitation + calcination (Ahmed et al., 2017, 168 citations [SRC-ED-011]). LFP CAM specific energy is estimated at 3-6 kWh/kg based on this analog and the lower calcination temperature (600-700 C versus 750-950 C for NMC). The project will generate the first primary LFP-specific energy data, addressing this documented research gap [CLM-021].

**Cross-industry DT quantitative benchmarks**: The projected performance improvements are grounded in demonstrated results across process industries, summarised by the deep-dive report [SRC-DT-REPORT, CLM-007]:

| Industry | Application | Scrap/waste reduction | Energy savings | Source |
|----------|------------|----------------------|----------------|--------|
| Battery cell production | Fraunhofer FFB DiBaZ | 10.3% scrap reduction | — | [CLM-017] |
| Industrial furnaces | TwinHeat (MINES Paris) | — | 10-15% energy | [CLM-016] |
| Steel production | Tata Steel DT | — | Cumulative savings >$1.4B | [SRC-DT-REPORT] |
| Chemical reactors | BASF | 20-30% unplanned downtime reduction | 5-8% energy | [SRC-DT-REPORT] |
| Pharmaceutical mfg | Various PAT implementations | 50% out-of-spec batch reduction | — | [SRC-DT-REPORT] |

The FAAM-ENI project targets the conservative end of these ranges (10-50% scrap reduction, 12-15% energy savings) recognising that LFP CAM synthesis is a new domain for DT deployment. These targets will be validated through progressive refinement during commissioning and the first year of operation.

#### Innovation Pillar 3: ISO 23247 + Multi-Scale Modelling for Chemical Manufacturing [NOV-003]
*Defensibility score: 7/10*

**What is new**: The first implementation of the ISO 23247 four-layer digital twin architecture for a thermal/chemical powder synthesis process, combined with a multi-scale physics-based modelling hierarchy spanning atomistic to plant scale.

All existing ISO 23247 implementations address **discrete manufacturing** — CNC machining [SRC-007, SRC-009], automotive body shop inspection [SRC-010], additive manufacturing [CLM-008]. Discrete manufacturing involves deterministic, geometry-driven operations where the DT models primarily represent kinematics, forces, and dimensional tolerances.

LFP CAM synthesis is fundamentally different: it is a **chemical process** involving thermally driven solid-state reactions, multi-phase transformations, atmosphere-dependent redox chemistry, and stochastic particle formation. The ISO 23247 framework must be extended to accommodate:

- **Reaction kinetics feedback**: Real-time tracking of multi-step solid-state reactions (Jander diffusion, Avrami nucleation, shrinking core) with activation energies ranging from 65-180 kJ/mol across decomposition, intermediate formation, olivine crystallisation, and carbon coating steps [CLM-020]
- **Atmosphere control**: pO2 monitoring and control at <10 ppm under flowing N2 — a safety-critical parameter where deviation causes irreversible Fe3+ surface oxidation and capacity loss
- **Multi-phase transformations**: Tracking the evolution from amorphous precursor mixture through intermediate phases (Li3Fe2(PO4)3, Fe2O3) to phase-pure olivine LiFePO4, with impurity phases (Li3PO4, Fe2P) as indicators of over-temperature excursions
- **Stochastic particle dynamics**: Population balance modelling of particle size distributions through spray drying (droplet formation, drying kinetics) and jet milling (breakage, classification), where the DT must predict distributions rather than deterministic states

This extension of ISO 23247 from discrete to chemical manufacturing is a generalisable contribution. The reference architecture developed for LFP CAM is directly applicable to other thermal/chemical powder processes (NMC CAM, anode materials, ceramic powders, pharmaceutical granulation), creating a replicable framework with broad impact beyond this specific project.

The multi-scale modelling chain bridges DFT-derived parameters through to plant-scale flowsheet optimisation. At each scale transition, the higher-fidelity model provides calibration data, material properties, or reduced-order surrogate models to the next level. The computational strategy ensures real-time capability: DFT and mesoscale simulations are performed offline (hours to days per run) to populate material property databases; continuum-scale CFD/PBM/reaction models are trained into neural network surrogates (millisecond inference); plant-scale optimisation uses these surrogates within the MPC framework.

#### Innovation Pillar 4: Pharmaceutical QbD/PAT for Battery CAM [NOV-005]
*Defensibility score: 6/10*

**What is new**: The first formal application of the ICH Q8-adapted Quality-by-Design (QbD) and Process Analytical Technology (PAT) framework to LFP cathode active material manufacturing, establishing systematic CQA-CPP linkages with in-line/at-line monitoring.

The pharmaceutical industry has spent two decades developing and validating the QbD approach under ICH Q8-Q11 guidelines: defining a Quality Target Product Profile (QTPP), identifying Critical Quality Attributes (CQAs), mapping Critical Process Parameters (CPPs), establishing a design space through systematic experimentation, and deploying PAT for real-time quality assurance. This framework has never been formally applied to battery CAM manufacturing [SRC-028, CLM-013, SRC-DT-REPORT].

**LFP-specific CQA-CPP mapping**: The project establishes the following systematic linkages:

| CQA | Target | Primary CPPs | Monitoring |
|-----|--------|-------------|------------|
| D10 particle size | 0.3-1.0 um | Milling: air pressure, classifier speed | Laser diffraction (at-line) |
| D50 particle size | 0.7-2.5 um | Spray drying: inlet/outlet T, feed rate, nozzle pressure; Milling: air pressure, classifier speed | FBRM (in-line), laser diffraction (at-line) |
| D90 particle size | 2.5-12.0 um | Milling: classifier speed, sieve aperture | Laser diffraction (at-line) |
| Specific surface area (SSA) | 10-14 m2/g | Calcination: T profile, dwell time; Spray drying: droplet size | BET (at-line) |
| Phase purity (olivine) | >98% | Calcination: T (max 700 C), pO2 (<10 ppm), dwell time | Raman (at-line), XRD (at-line) |
| Carbon content | 1.0-1.8 wt% | Glucose loading (Step 1), calcination T profile | Raman D/G ratio (at-line), elemental analysis |
| Fe2+/Fe3+ ratio | >0.95 | Calcination: pO2 control, cooling rate | Mossbauer or XPS (at-line) |
| Discharge capacity (0.1C) | >=155 mAh/g | All above (integrated quality) | Electrochemical testing (off-line), DT prediction (real-time) |
| Discharge capacity (1C) | >=140 mAh/g | All above (integrated quality) | Electrochemical testing (off-line) |
| ICE | ~98% | Calcination: T profile, atmosphere; Carbon coating quality | Electrochemical testing (off-line) |
| Moisture | <750 ppm | Packaging: N2 environment, sealing | Karl Fischer (at-line) |
| Magnetic impurities | <=1000 ppb | Demagnetisation field strength, milling media quality | Magnetic susceptibility (at-line) |
| Tap density | 1.0-1.4 g/cm3 | Spray drying: morphology control; Milling: classification | Tap density (at-line) |
| Pellet density | >=2.40 g/cm3 | Calcination: sintering control; Particle morphology | Density measurement (at-line) |
| Electrode press density | >=2.30 g/cm3 | Particle morphology, PSD control | Press density measurement (at-line) |
| Particle morphology | Spherical, minimal aggregation | Spray drying: T, feed concentration | SEM/image analysis (off-line), DT prediction |

The QbD framework transforms LFP CAM manufacturing from recipe-based empirical control to model-predictive design-space control. Instead of fixing process parameters and testing the result, the DT continuously predicts product quality from current process state and adjusts parameters to maintain operation within the validated design space. This is the conceptual leap that pharmaceutical manufacturing achieved with PAT — now applied to battery materials for the first time.

**Sensor challenges and mitigation**: Direct transfer of pharmaceutical PAT to LFP calcination faces practical constraints: Raman probes require sapphire windows that foul at 600-700 C; FBRM cannot survive calcination temperatures; O2 sensors drift at high temperature [SRC-DT-REPORT]. The project addresses these through a **hybrid in-line/at-line strategy**: true in-line monitoring where sensors can operate (spray drying, milling, packaging) and rapid at-line sampling with automated transfer for calcination-related CQAs (phase purity, carbon quality). The DT's virtual sensing capability bridges the gaps — physics-based models predict calcination-stage CQAs from measurable in-line parameters (temperature, atmosphere, time), validated against periodic at-line measurements.

### Mandatory Innovation Dimensions

The Innovation Fund evaluation requires evidence of innovation across plant design, operating approach, construction, performance/quality, reliability/availability, maintenance, and economics. The following table maps the project's innovations to each dimension:

| Dimension | Innovation beyond SOTA | Evidence |
|-----------|----------------------|----------|
| **Plant design** | Progressively electrified thermal processing (HTHP + electric RHK, with pathway to full electrification); ISO 23247 DT architecture integrated from design phase; PAT sensor network embedded in process equipment; 4 modular lines x 12.5 kton/yr for 50 kton/yr total capacity | No existing LFP CAM plant uses electrified process heat or integrated DT [CLM-005, GAP-003] |
| **Operating approach** | Closed-loop MPC replacing recipe-based control; real-time quality prediction from physics-based surrogates; automated process adjustment within design space | Current SOTA: empirical, recipe-based, offline QC [CLM-013, SRC-028] |
| **Construction** | Brownfield conversion of Eni industrial site; accelerated timeline leveraging existing infrastructure and permitting precedent | Site-specific advantage enabling FC within 2 years, EiO within 4 years |
| **Performance/quality** | Target CQAs: D50 0.7-2.5 um, SSA 10-14 m2/g, >=155 mAh/g capacity (0.1C), >=140 mAh/g (1C), >98% olivine purity, carbon 1.0-1.8 wt%, ICE ~98%; achieved through DT-driven process control | DT benchmarks: 10-50% scrap reduction [CLM-007, CLM-017] |
| **Reliability/availability** | Predictive maintenance via DT (20-50% unplanned downtime reduction); condition-based equipment monitoring; virtual sensing for inaccessible parameters | Cross-industry DT downtime reduction demonstrated [CLM-007] |
| **Maintenance** | Condition-based monitoring replacing calendar-based schedules; DT-derived equipment health indicators; degradation prediction for heating elements, sensors | TwinHeat predictive maintenance for furnace elements [CLM-016] |
| **Economics** | Reduced scrap and energy costs; quality consistency enabling premium pricing; lower total cost of ownership for electrified vs gas equipment (no fuel price volatility) | Energy savings 12-15% [CLM-007]; thermal efficiency advantage 1.6-3.8x [CLM-023] |

### TRL Progression

| Component | Start TRL | End TRL | Evidence for current TRL | Advancement pathway |
|-----------|-----------|---------|-------------------------|-------------------|
| LFP solid-state synthesis | 7 | 9 | Established industrial route used by all major Chinese producers [SRC-011, SRC-022]. The project's technology licensor provides proven process know-how for the solid-state synthesis route, bridging from TRL 7 (demonstrated industrial route) to the specific Brindisi plant configuration. | Process qualification at Brindisi; product certification with cell manufacturers |
| Electrified calcination (electric RHK) | 5-6 | 7-8 | Electric roller hearth kilns commercially available (Kanthal, NGK) and validated for NMC at higher temperatures [SRC-ED-009, SRC-ED-010, SRC-ED-023]; not demonstrated for LFP-specific chemistry/atmosphere | System integration with LFP process; validation of product quality under electric heating; long-term reliability demonstration |
| HTHP spray drying | 5 | 7 | HTHP demonstrated at COP 3.04-3.6 in peer-reviewed studies [SRC-ED-004, SRC-ED-005]; not integrated with LFP slurry drying | Integration with LFP precursor spray drying; scale-up validation; thermal efficiency verification |
| DT for CAM synthesis | 3-4 | 6-7 | Individual physics-based models validated (ARTISTIC for electrodes [SRC-004]; TwinHeat for furnaces [SRC-DT-REPORT]; Ma et al. for sintering [SRC-014]); no integrated LFP CAM DT exists [CLM-005] | Model integration; sensor fusion validation; closed-loop MPC commissioning; industrial operation |
| ISO 23247 for powder manufacturing | 3 | 6 | Standard defined and validated for discrete manufacturing only [SRC-007, SRC-009, SRC-010, CLM-008] | Extend to chemical/powder processes; validate data exchange; demonstrate real-time capability |
| PAT/QbD for LFP | 4 | 7 | Pharmaceutical PAT mature (ICH Q8-Q11); LFP CQA/CPP mapping documented [SRC-DT-REPORT]; sensor technologies exist individually | Formal CQA-CPP validation; design space establishment; RTRT implementation |

### Barriers to Overcome

**Technological barriers:**

1. **Scaling multi-scale models to real-time**: The DFT-to-plant modelling hierarchy requires surrogate models at each scale transition to achieve real-time inference (<1 second). Training accurate surrogates requires extensive high-fidelity simulation campaigns. The risk is that surrogate fidelity is insufficient for closed-loop control — mitigated by the hybrid approach (physics-based + data-driven corrections from sensor data) and progressive refinement during commissioning.

2. **Sensor reliability at >600 C**: Raman spectroscopy probes face sapphire window fouling during calcination; FBRM cannot operate above its thermal limit; zirconia O2 sensors drift at sustained high temperatures. Mitigation: hybrid in-line/at-line strategy with virtual sensing to bridge measurement gaps; sensor maintenance scheduling informed by DT-predicted degradation rates.

3. **DT-process coupling latency**: For effective MPC, the sensor-to-actuator control loop must complete within the process time constant. For calcination (thermal time constant ~minutes), this is achievable. For spray drying (droplet drying time ~seconds), edge computing with pre-computed lookup tables from surrogate models is required. Target: <100 ms sensor-to-prediction latency at edge nodes; <5 second prediction-to-actuation for all MPC loops.

4. **LFP-specific atmosphere control under electric heating**: Maintaining pO2 <10 ppm in an electric roller hearth kiln requires careful sealing and N2 flow design. Gas-fired kilns inherently consume some O2 through combustion; electric kilns must rely entirely on inert gas purging. This is a design engineering challenge rather than a fundamental barrier — electric kilns for NMC operate at even stricter atmosphere requirements.

**Economic barriers:**

1. **Higher CAPEX for electrified equipment**: Electric roller hearth kilns and HTHP systems carry higher upfront capital costs compared to gas-fired alternatives. The total cost of ownership (TCO) analysis favours electrification when gas price volatility, carbon pricing (EU ETS), and avoided stranded asset costs are included. The Innovation Fund grant directly addresses this CAPEX barrier.

2. **DT development cost**: Building and validating the multi-scale modelling framework, sensor network, data infrastructure, and MPC system represents a significant R&D investment that is not recoverable from a single plant. The Innovation Fund co-financing and the replicability of the DT framework to future plants (and other CAM chemistries) justify this investment.

### Why This Scale Is Most Appropriate

The proposed scale — a commercial production plant, not a pilot or demonstration unit — is the most appropriate for validating the integrated innovation package because:

1. **DT value proposition requires production-scale variability**: Digital twins deliver their greatest value by managing process variability that emerges at production volumes and duration. A pilot plant (TRL 5-6) lacks the throughput, batch counts, and operational duration to generate the data required for DT model validation and MPC tuning. Production scale is essential to demonstrate the 10-50% scrap reduction and 12-15% energy savings claimed.

2. **Electrification economics are scale-dependent**: The thermal efficiency advantage of electric kilns (95% vs 25-60% [CLM-023]) translates to absolute energy cost savings proportional to production volume. At pilot scale, the fixed costs of HTHP and electric RHK infrastructure overwhelm the variable energy savings. Commercial scale is required for economic viability.

3. **Strategic autonomy requires production volume**: The EU's dependency on Chinese LFP CAM [CLM-001] is not addressed by pilots. The Innovation Fund explicitly targets manufacturing facilities that establish domestic production capacity aligned with NZIA benchmarks. FREYR's funded project targets 30,000 t/yr [SRC-025], confirming that commercial scale is the expected ambition level.

4. **Precedent**: The Innovation Fund has not funded LFP CAM pilots — it has funded a production-scale facility (FREYR, EUR 122M). This project is positioned at the same ambition level, differentiated by electrification, DT integration, and geographic positioning.
