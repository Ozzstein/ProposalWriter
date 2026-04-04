# FEASIBILITY STUDY

---

**Project name**: FAAM-ENI Circular Energy
**Acronym**: FACE
**Call**: INNOVFUND-2025-NZT-CLEAN-TECH-MANUFACTURING
**Version**: 1.0
**Date**: April 2026

---

## 1. Project Description

### 1.1 Overview

The FAAM-ENI Circular Energy (FACE) project will design, construct, commission, and operate the first fully electrified lithium iron phosphate (LiFePO4, LFP) cathode active material (CAM) manufacturing plant in Italy and Southern Europe. The plant will be located at Eni's brownfield industrial site in Brindisi, Puglia, and will produce battery-grade LFP CAM powder for supply to European lithium-ion battery cell manufacturers serving the electric vehicle (EV) and grid-scale energy storage system (ESS) markets.

The project is implemented by a two-partner consortium: FIB (FAAM), the coordinator and battery manufacturer responsible for plant construction and operation, and Eni, the brownfield site owner contributing process engineering expertise and energy supply infrastructure.

The FACE plant employs a solid-state synthesis route -- the dominant industrial process for LFP CAM globally [CLM-009, SRC-011] -- with two defining technical differentiators that position it beyond the current state-of-the-art:

1. **Fully electrified thermal processing**. The two energy-intensive production steps -- spray drying and calcination -- are powered entirely by electricity, replacing the natural gas-fired equipment used universally in incumbent Chinese production facilities [CLM-001, CLM-023]. Electric roller hearth kilns achieve 95% thermal efficiency versus 25-60% for gas-fired systems [CLM-023, SRC-ED-009], and heat pump-assisted spray drying delivers COP 3.0-3.6 [SRC-ED-004, SRC-ED-005]. This electrified design eliminates on-site Scope 1 combustion emissions and positions the plant to capitalise on Italy's grid decarbonisation trajectory, delivering 55-70% GHG avoidance versus gas-fired benchmarks by 2030 and exceeding 80% by 2035 [CLM-026, CLM-030].

2. **ISO 23247-compliant digital twin (DT)**. An integrated, real-time digital twin framework governs the entire production chain from raw material dosing through calcination to final packaging. The DT implements the ISO 23247 four-layer architecture [CLM-008, SRC-007] with multi-scale physics-based models spanning atomistic (DFT) to plant scale (flowsheet simulation) [CLM-018], Process Analytical Technology (PAT) sensor networks for in-line and at-line quality monitoring [CLM-019], and model-predictive control (MPC) for closed-loop process optimisation. Cross-industry benchmarks project 10-50% scrap reduction, 12-15% energy savings, and >40% batch-to-batch variability reduction [CLM-007, CLM-016, CLM-017].

3. **EU strategic autonomy**. China controls over 99% of global LFP CAM production capacity [CLM-001] and has imposed escalating export controls on cathode technology (July 2025) and production equipment (October 2025) [CLM-002]. No EU-based company currently produces LFP CAM [CLM-003]. The FACE plant directly addresses this critical supply chain vulnerability, complementing FREYR Battery's funded but not-yet-operational project in Finland [CLM-004, CLM-029].

### 1.2 Technology and Product Description

The plant produces battery-grade LiFePO4/C composite powder -- a cathode active material with an olivine crystal structure (space group Pnma) that delivers high safety, long cycle life (>2,000 cycles), and competitive cost for EV standard-range and stationary ESS applications [SRC-011, SRC-015].

The product meets the following Critical Quality Attribute (CQA) specifications, established through a Quality-by-Design (QbD) framework adapted from pharmaceutical manufacturing (ICH Q8) [CLM-009, SRC-DT-REPORT]:

| CQA | Target | Specification | Test Method |
|-----|--------|---------------|-------------|
| D50 particle size | 1-3 um | +/- 0.5 um | Laser diffraction (ISO 13320) |
| BET surface area | 12-18 m2/g | +/- 3 m2/g | N2 adsorption (ISO 9277) |
| Tap density | 1.0-1.4 g/cm3 | >1.0 g/cm3 | ASTM B527 |
| Phase purity (olivine) | >98% | Min 97% | XRD Rietveld refinement |
| Carbon content | 1.5-3.0 wt% | +/- 0.5 wt% | TGA / combustion analysis |
| Fe2+/Fe3+ ratio | >0.95 | Min 0.90 | Mossbauer spectroscopy / XPS |
| Discharge capacity | >155 mAh/g (C/10) | Min 150 mAh/g | Half-cell electrochemical test |
| Moisture | <200 ppm | Max 500 ppm | Karl Fischer titration |
| Carbon D/G ratio | 0.8-1.2 | Range | Raman spectroscopy |

These specifications target Tier-1 European cell manufacturers (e.g., PowerCo, Verkor, Northvolt, ACC) who require consistent, battery-grade LFP CAM with full traceability -- a requirement that will be mandated by the EU Battery Regulation (2023/1542) Battery Passport from 2027.

### 1.3 Innovation Pillars

The project rests on three mutually reinforcing innovation pillars:

**Pillar 1 -- Electrification of process heat**: Replacing natural gas with electricity for spray drying and calcination eliminates Scope 1 combustion emissions, provides superior temperature control precision (+/-1 C vs +/-5-10 C for gas burners) [SRC-ED-018], and locks in a future-proof infrastructure design that avoids stranded fossil fuel assets [CLM-030].

**Pillar 2 -- Integrated digital twin**: The first digital twin for upstream CAM powder synthesis fills a documented gap between electrode-level DTs (ARTISTIC platform [SRC-004]) and cell-level DTs (Fraunhofer DiBaZ) [CLM-005]. The DT enables real-time quality prediction, closed-loop MPC, predictive maintenance, and accelerated process optimisation during ramp-up.

**Pillar 3 -- EU strategic autonomy**: The plant establishes domestic LFP CAM supply for European cell manufacturers, reducing single-source dependency on China [CLM-001] and contributing to NZIA manufacturing benchmarks.

### 1.4 Block Flow Diagram

The production process comprises seven sequential unit operations. *See Figure 1 in the Word document for the graphical block flow diagram.*

| Step | Unit Operation | Key Equipment | Innovation Element |
|------|---------------|---------------|-------------------|
| 1 | Raw material dosing and dispersion | Gravimetric feeders, stirred dispersion tank | DT-monitored stoichiometry |
| 2 | Sand milling + magnetic particle removal | Horizontal bead mill, electromagnetic demagnetiser | In-line FBRM particle size monitoring |
| 3 | Spray drying (ELECTRIFIED) | Electric spray dryer with HTHP air pre-heating | Electrified thermal processing; DT-controlled drying parameters |
| 4 | Calcination (ELECTRIFIED) | Electric roller hearth kiln, N2 atmosphere | Electrified calcination; DT-driven temperature profile MPC |
| 5 | Jet milling | Air-flow jet mill | DEM-based DT model for milling optimisation |
| 6 | Classification + demagnetisation | Ultrasonic vibrating sieve, electromagnetic separator | At-line quality verification integrated with DT |
| 7 | Automated packaging | N2-blanketed packaging line | Full traceability, Battery Passport data capture |

The process flow is: raw materials (FePO4 + Li2CO3 + glucose) enter at Step 1, water is removed at Step 3 (spray drying), the solid-state reaction occurs at Step 4 (calcination at 650-700 C under N2), particle size is refined at Steps 5-6, and finished LiFePO4/C powder exits at Step 7. DT integration points exist at every step, with the most critical being Steps 3 (spray drying) and 4 (calcination), where process parameters directly determine final product quality [CLM-009].

---

## 2. Background Information (Existing Situation)

### 2.1 Eni Brindisi Brownfield Site

The project is sited on an existing industrial property owned by Eni S.p.A. in Brindisi, Puglia, southern Italy. The Brindisi complex has operated as an Eni petrochemical and energy site for several decades, providing established industrial infrastructure including:

- High-voltage grid connection and electrical distribution capacity
- Industrial water supply and wastewater treatment facilities
- Road and rail access for logistics
- Proximity to Brindisi port for maritime raw material supply
- Established relationships with local regulatory authorities (Regione Puglia, ARPA Puglia)
- Existing environmental baseline data and monitoring systems
- Industrial zoning classification eliminating residential proximity concerns

[ASSUMPTION: The specific area within the Eni Brindisi site allocated to the FACE plant, including total available land area (m2), existing building structures to be repurposed vs demolished, and current operational status of the site (active, partially active, or decommissioned), must be confirmed by the project team.]

The brownfield nature of the site offers material advantages: reduced civil works scope compared to greenfield construction, accelerated permitting based on existing industrial zoning and environmental authorisation precedent, and existing utility connections that reduce infrastructure CAPEX and lead time.

### 2.2 Global LFP CAM Market Context

The global LFP CAM market presents a stark geographic concentration. China controls over 99% of global LFP CAM production capacity [CLM-001, SRC-022, SRC-023]. The dominant producers -- CATL, BYD, Gotion High-Tech, and Dynanonic -- operate exclusively gas-fired production facilities using natural gas rotary kilns for calcination and gas-heated spray dryers [SRC-022, SRC-PAT-005].

This concentration has become an acute supply chain risk following China's imposition of export licensing requirements on 4th-generation LFP cathode technology in July 2025 and the broadening of these controls to battery cells, precursors, anode materials, and production equipment in October 2025 [CLM-002, SRC-024]. The German Council on Foreign Relations (DGAP) has identified EU LFP CAM manufacturing as a critical strategic gap [SRC-024], and the European Parliament Research Service has recommended urgent domestic production capacity development [SRC-023].

### 2.3 European LFP CAM Production Status

As of late 2025, no European company operates a commercial LFP CAM production line [CLM-003]. The landscape comprises:

- **FREYR Battery (Finland)**: Received a EUR 122M Innovation Fund grant (October 2024) for a planned 30,000 t/yr LFP CAM facility in Vaasa, Finland [SRC-025]. However, FREYR has not reached Final Investment Decision (FID) for Vaasa and is currently prioritising its US Giga America facility [CLM-029]. The Vaasa project should be treated as a medium-term option with non-trivial schedule and financing risk.

- **CATL**: Expanding cell production within Europe but LFP CAM production status in Europe is unclear [SRC-023]. CATL's European operations primarily involve cell assembly using imported Chinese CAM.

- **Umicore**: Produces NMC cathode materials in Poland but does not manufacture LFP CAM [SRC-023].

- **PowerCo, Verkor, ACC, Northvolt**: European cell manufacturers that require domestic LFP CAM supply but do not produce their own CAM.

The FACE project addresses this gap as the first LFP CAM production facility in Italy and Southern Europe [CLM-022], providing geographic diversification within the EU LFP supply landscape alongside FREYR's Northern European site.

### 2.4 FIB/FAAM Capabilities

FIB (Fabbrica Italiana Batterie, incorporating the FAAM brand) is an established Italian battery manufacturer with expertise in lead-acid and lithium-ion battery production, including cell assembly, module integration, and battery management systems. FIB's existing manufacturing infrastructure and quality management systems provide the organisational foundation for upstream expansion into CAM production.

[ASSUMPTION: FIB/FAAM's current battery manufacturing capacity (MWh/year), number of manufacturing sites, ISO certifications (ISO 9001, ISO 14001, IATF 16949), and specific prior experience with LFP chemistry at cell level must be confirmed by the project team.]

---

## 3. Location Analysis and Strategic Approach

### 3.1 Site Location

**Brindisi, Puglia, Italy** -- The FACE plant is located within Eni's existing industrial complex in the Brindisi industrial zone. Key site attributes:

| Factor | Description |
|--------|-------------|
| **Geographic coordinates** | [ASSUMPTION: Exact coordinates to be provided] |
| **Industrial zone** | Established industrial area with appropriate zoning |
| **Port access** | Brindisi port -- Mediterranean maritime hub for raw material import (FePO4, Li2CO3 from global suppliers) and product export |
| **Grid connection** | High-voltage connection to Terna (Italian TSO) grid; Puglia region has excellent renewable energy potential |
| **Solar irradiance** | ~1,700 kWh/m2/yr -- among the highest in Italy, favourable for on-site PV or regional PPA |
| **Road/rail** | Connected to A14 motorway and national rail network for domestic logistics |
| **Labour market** | Puglia convergence region with skilled industrial workforce and proximity to Politecnico di Bari and Universita del Salento |
| **Climate** | Mediterranean climate; minimal freeze-thaw impact on construction scheduling |

The Brindisi location provides strategic advantages for serving Southern European and Mediterranean battery cell manufacturers. The plant's proximity to potential customers in Italy (e.g., ITALVOLT, Eni-FIB internal demand), Spain, and Southern France reduces logistics costs and carbon footprint compared to Northern European or Asian supply.

### 3.2 Links to Other Projects

The FACE project is positioned within a broader ecosystem of EU battery supply chain initiatives:

- **EU Battery Alliance**: The project contributes to the Alliance's objective of establishing a complete domestic battery value chain within the EU, specifically addressing the upstream CAM production gap.

- **IPCEI on Batteries (Hy2Use, EuBatIn)**: While FACE is not an IPCEI project, it complements IPCEI-funded cell manufacturing facilities by providing a domestic CAM supply source.

- **Eni's Energy Transition Strategy**: The Brindisi site conversion from fossil fuel operations to clean-tech manufacturing directly implements Eni's strategic pivot toward decarbonisation. Eni's investment provides co-financing leverage and demonstrates energy company commitment to the battery value chain.

- **FREYR Battery (Finland)**: FACE and FREYR together would establish a two-node European LFP CAM supply base with geographic diversification (Nordic + Mediterranean), reducing single-point-of-failure risk in EU supply chains.

### 3.3 EU Legislation Compliance

**EU Battery Regulation (2023/1542)**

The FACE plant is designed for full compliance with the EU Battery Regulation, which introduces progressively stringent requirements:

| Requirement | Timeline | FACE Compliance Approach |
|-------------|----------|--------------------------|
| Carbon footprint declaration | 2025 (EV batteries) | DT provides complete process energy and material traceability; electrified production enables low carbon footprint |
| Carbon footprint performance class | 2026 | Electrified production with Italian grid trajectory positions FACE product in top performance classes |
| Battery Passport | 2027 | DT data infrastructure provides full batch traceability from precursor receipt to product shipment; compliant data model |
| Recycled content targets | 2031 (Li 6%), 2036 (Li 12%) | Plant design accommodates integration of recycled lithium precursors in future; modular process allows feedstock flexibility |
| Due diligence (OECD) | 2025 | Responsible sourcing policy for all precursors; supplier audit programme |

**Net-Zero Industry Act (NZIA)**

The NZIA establishes EU manufacturing benchmarks for clean technologies, explicitly including battery and energy storage manufacturing. FACE directly contributes to the NZIA objective of ensuring at least 40% of EU demand for clean technologies is met by domestic manufacturing by 2030. LFP CAM is classified as a strategic net-zero technology component.

**REACH**

All chemical substances used in the production process (iron phosphate, lithium carbonate, glucose, nitrogen) are either pre-registered under REACH or are exempt (N2, glucose as food-grade commodity). No novel chemical substances requiring REACH registration are introduced by the FACE process.

### 3.4 Regulatory Requirements and Permitting Strategy

The project requires the following regulatory authorisations under Italian law:

| Permit | Authority | Description | Estimated Timeline |
|--------|-----------|-------------|-------------------|
| VIA (Valutazione di Impatto Ambientale) | Ministero dell'Ambiente e della Sicurezza Energetica (MASE) / Regione Puglia | Environmental Impact Assessment for new industrial installation | 12-18 months |
| AIA (Autorizzazione Integrata Ambientale) | Regione Puglia | Integrated Environmental Authorisation under Industrial Emissions Directive (IED) | 6-12 months (may run in parallel with VIA) |
| Permesso di Costruire | Comune di Brindisi | Building permit for new construction and site modifications | 3-6 months |
| Certificato di Prevenzione Incendi | Vigili del Fuoco | Fire safety certification | 2-4 months |
| Autorizzazione emissioni in atmosfera | Regione Puglia / ARPA | Atmospheric emission permit (limited scope -- electrified plant has minimal process emissions) | Included in AIA |

[ASSUMPTION: The current permitting status for the FACE plant is assumed to be at pre-application stage. If Eni has initiated any pre-consultation meetings with MASE or Regione Puglia, or if the brownfield site has existing environmental authorisations that can be amended rather than obtained de novo, this would materially accelerate the permitting timeline. The project team should confirm the actual permitting status and strategy.]

**Permitting mitigation strategy**:
- Early engagement with Regione Puglia and MASE permitting authorities
- Leverage Eni's decades-long relationship with Brindisi local authorities
- Engage experienced Italian environmental permitting consultants (e.g., ERM, Arcadis)
- The electrified process significantly simplifies the atmospheric emissions component of the AIA (no combustion emissions, no NOx/SOx/particulate from gas firing)
- Schedule buffer of 3 months between expected permit receipt and construction start

### 3.5 Intellectual Property Strategy

**Background IP**:

| Partner | Background IP | Licensing |
|---------|--------------|-----------|
| FIB (FAAM) | Battery manufacturing know-how; cell assembly and testing protocols; quality management systems | Contributed to project under consortium agreement; no royalties |
| Eni | Process engineering expertise; brownfield site engineering; energy systems design; industrial digitalisation capabilities | Contributed to project under consortium agreement; no royalties |

Neither FIB/FAAM nor Eni holds active patents in LFP CAM synthesis, process equipment, or digital twin manufacturing [CLM-015]. Both partners are technology acquirers in this specific domain, which eliminates intra-consortium IP conflicts.

**Foreground IP**:

The project will generate foreground IP in three domains:

1. **DT framework for CAM manufacturing (NOV-001)**: The ISO 23247-compliant DT architecture, multi-scale model library, sensor fusion algorithms, and MPC control strategies. This represents the core patent-filing opportunity. A patent application covering the novel combination of ISO 23247 architecture with multi-scale physics-based modelling for real-time process control in chemical powder manufacturing is planned [CLM-014].

2. **Electrified LFP CAM process parameters (NOV-002)**: The specific process parameter sets (temperature profiles, atmosphere control, spray drying conditions) optimised for electrified equipment. These constitute trade secrets rather than patentable inventions, protected through confidentiality agreements.

3. **PAT methodology for LFP (NOV-005)**: The CQA-CPP mapping, sensor deployment strategy, and design space definition for LFP CAM manufacturing. Publication strategy: peer-reviewed papers in journals such as Journal of Power Sources and Batteries to establish scientific priority, with key implementation details retained as know-how.

**Freedom-to-operate assessment**: Medium overall [CLM-014]. The core DT + electrification combination occupies a patent white space with no blocking IP identified. Manageable risks include:

| Patent | Assignee | Risk Level | Mitigation |
|--------|----------|------------|------------|
| EP2360117B1 | LG Chem | Medium | Active EU patent on LFP morphology (D50 5-100 um). Expires ~2029. Product specification review to ensure non-infringement. |
| EP4222563A4 | AspenTech | Medium | Industrial DT architecture patent. If AspenTech platform is used, licensed automatically. |
| US20230261188 | Mitra Future Tech | Low | Pending, covers R&D workflow not in-line process control. |

[ASSUMPTION: A comprehensive Chinese-language CNIPA patent search is recommended to assess the IP position of CATL, BYD, Gotion, and Dynanonic. English-language searches do not adequately cover Chinese patent filings in this domain.]

**Confidentiality provisions**: The consortium agreement establishes mutual NDA obligations between FIB and Eni, with specific provisions for: (i) background IP protection; (ii) foreground IP ownership (inventor institution owns, partner receives royalty-free licence for project purposes); (iii) publication approval process (30-day review period for patentability assessment); and (iv) post-project exploitation rights.

### 3.6 Public Acceptance

The project benefits from strong public acceptance conditions:

- **Industrial zoning**: The Brindisi site is located in an established industrial zone, remote from residential areas, eliminating NIMBY concerns.
- **Job creation**: The plant creates direct manufacturing employment in a Puglia convergence region with above-average unemployment, aligned with EU Cohesion Policy objectives.
- **Clean-tech narrative**: The conversion of a fossil fuel site to clean-tech battery material manufacturing is positively received by local and regional stakeholders as a tangible example of just energy transition.
- **No hazardous emissions**: The electrified process eliminates combustion-related emissions (NOx, SOx, PM). Process off-gases (CO2 from carbonate decomposition, water vapour) are captured and treated through standard industrial scrubbing.

### 3.7 Environmental Impacts Throughout the Lifecycle

**Construction phase**: Standard industrial construction impacts (noise, dust, vehicle movements) mitigated through construction management plan. Brownfield site reduces land-use change impact.

**Operational phase**:
- No on-site combustion emissions (electrified process)
- Process CO2 from Li2CO3 decomposition during calcination (stoichiometric, ~0.28 t CO2 per t LFP CAM)
- N2 gas consumption for inert atmosphere (recycled via closed-loop system with scrubbing)
- Water consumption for slurry preparation (recycled via spray dryer condensate recovery)
- Solid waste: off-specification product (recycled to precursor stage), spent grinding media (metal recycling), filter media (industrial waste disposal)

**End-of-life phase**: Plant equipment is standard industrial equipment with established decommissioning and recycling pathways. No hazardous legacy comparable to petrochemical operations.

---

## 4. Objectives

The FACE project pursues five SMART objectives that collectively define the technical, environmental, and commercial success criteria:

| # | Objective | Metric | Target | Timeline | Verification |
|---|-----------|--------|--------|----------|-------------|
| O1 | Commission the first electrified LFP CAM production line in Italy | Entry into Operation (EiO) | Operational plant producing saleable product | M48 (4 years from grant agreement) | Independent third-party commissioning verification |
| O2 | Deploy an ISO 23247-compliant digital twin achieving real-time process control | DT latency: sensor-to-prediction | <1 second at edge nodes; <5 second prediction-to-actuation for all MPC loops | M42 (DT operational before full plant EiO) | Performance testing against ISO 23247 conformance criteria |
| O3 | Demonstrate >=50% relative GHG emission avoidance versus gas-fired reference | Relative GHG avoidance (Innovation Fund methodology) | >=50% by Year 1 of operation (using projected grid intensity at EiO) | Year 1 post-EiO (verified annually) | Innovation Fund GHG calculator; third-party LCA verification |
| O4 | Achieve product quality meeting battery-grade CQA specifications | CQA compliance rate | D50 1-3 um, capacity >155 mAh/g, phase purity >98% -- >=95% batch compliance | M54 (6 months post-EiO) | Statistical process capability analysis (Cpk > 1.33 for all CQAs) |
| O5 | Reduce batch-to-batch variability by >=40% through DT-enabled closed-loop control | Coefficient of variation (CV) of key CQAs (D50, capacity, phase purity) | CV reduction >=40% versus open-loop baseline | Year 2 of operation | Statistical comparison: first 6 months (open-loop baseline) vs Year 2 (DT-optimised) |

These objectives are consistent with the Innovation Fund scoring criteria: O1 addresses project maturity (EiO within 4 years for bonus points); O3 directly addresses the GHG emission avoidance criterion (>=50% minimum); O4 and O5 address innovation impact and product quality; and O2 provides the technical enabler for O4 and O5.

---

## 5. Resources and Feedstock Availability

### 5.1 Supply Chain Analysis

#### 5.1.1 Raw Material Requirements

The solid-state LFP synthesis route requires three primary precursors plus process utilities:

| Material | Function | Approx. Quantity per t LFP CAM | Supply Category |
|----------|----------|-------------------------------|-----------------|
| Iron phosphate (FePO4) | Iron and phosphorus source | ~1.0-1.05 t (stoichiometric + 2-5% excess) | Commodity industrial chemical |
| Lithium carbonate (Li2CO3) | Lithium source | ~0.24-0.26 t (stoichiometric + 2-5% Li excess) | Critical raw material |
| Glucose (C6H12O6) | Carbon source for in-situ coating | 50-150 kg (5-15 wt% of total solids) | Food-grade commodity |
| Nitrogen gas (N2) | Inert atmosphere for calcination | [ASSUMPTION: XX Nm3 per t -- depends on kiln volume, purge rate, and N2 recycling efficiency] | Industrial gas |
| Deionised water | Slurry preparation medium | [ASSUMPTION: XX m3 per t -- recycled via spray dryer condensate recovery] | On-site treatment |
| Electricity | All process heat + milling + utilities | ~3-6 kWh/kg LFP CAM [CLM-027] (~3,000-6,000 kWh/t) | Grid + PPA |

#### 5.1.2 Iron Phosphate (FePO4) Supply

Iron phosphate is produced globally through the reaction of iron salts (FeSO4, FeCl2) with phosphoric acid or sodium phosphate. The supply base is concentrated in China but with growing non-Chinese capacity:

- **Chinese suppliers**: Largest global capacity. Multiple Tier-1 suppliers (Guizhou Anda, Yunnan Copper) with established export channels.
- **European suppliers**: Limited current capacity. Chemical companies such as Budenheim (Germany) and Prayon (Belgium) produce iron phosphate for food and pharmaceutical applications; battery-grade specifications may require qualification.
- **Diversification strategy**: Dual-sourcing from at least one Chinese and one non-Chinese supplier, with strategic inventory buffer (minimum 3 months).

[ASSUMPTION: Specific supplier names, contracted volumes, pricing structure, and qualification status must be confirmed by the procurement team. Long-term supply agreements with price hedging mechanisms should be negotiated before FID.]

#### 5.1.3 Lithium Carbonate (Li2CO3) Supply

Lithium carbonate is classified as a critical raw material under the EU Critical Raw Materials Act (CRMA). The global supply is dominated by Australia (spodumene mining) and South America (brine extraction), with Chinese conversion capacity controlling a large share of refined lithium carbonate production.

**Procurement strategy**:
- Primary sourcing from established lithium producers with European trading operations (Albemarle, SQM, Pilbara Minerals via offtake)
- EU sourcing option: European lithium projects in development (Vulcan Energy in Germany, Imerys in France, Savannah Resources in Portugal) may provide domestic supply by 2028-2030
- Spot market access as backup through LME lithium carbonate contract (launched 2023)
- Strategic inventory: minimum 3 months of lithium carbonate buffer stock
- Price hedging: forward contracts or financial hedging where commercially available

[ASSUMPTION: Lithium carbonate pricing is highly volatile (ranged from ~USD 15,000/t to ~USD 80,000/t between 2022-2025). The specific contracted price and hedging strategy must be defined in the business plan. OPEX sensitivity to lithium price should be modelled at +/-50%.]

#### 5.1.4 Glucose

Glucose is a food-grade commodity chemical produced from corn or wheat starch hydrolysis. Supply is abundant, globally diversified, and price-stable. European suppliers include Cargill, Roquette, and Tereos. No supply chain risk is identified.

#### 5.1.5 Nitrogen Gas

High-purity nitrogen (>99.99%) is required for the inert calcination atmosphere. Supply options:

- **On-site PSA (Pressure Swing Adsorption) generator**: Produces N2 from compressed air at >99.5% purity. Preferred for large-volume continuous demand. CAPEX ~EUR 200-500k depending on capacity. Operating cost ~EUR 0.03-0.05/Nm3.
- **Bulk liquid N2 delivery**: From industrial gas suppliers (Air Liquide, Linde, SOL Group -- all with operations in southern Italy). Higher purity (>99.999%) but higher operating cost (~EUR 0.10-0.20/Nm3).
- **Hybrid approach**: On-site PSA for base load with bulk liquid top-up for peak demand and ultra-high-purity applications.

[ASSUMPTION: The specific N2 supply configuration, consumption rate, and cost must be confirmed by process engineering based on kiln volume, purge rate, and N2 recycling efficiency.]

#### 5.1.6 Electricity

Electricity is the primary energy input for the electrified plant, consumed across spray drying (~30-40% of total), calcination (~40-50%), milling (~10-15%), and auxiliaries (~5-10%).

**Supply strategy**:
- Grid connection via Terna (Italian TSO) at high voltage. Existing grid infrastructure at the Eni Brindisi site provides adequate capacity.
- Long-term Power Purchase Agreement (PPA) with a renewable electricity provider to lock in costs and ensure low-carbon supply. Puglia's excellent solar irradiance (~1,700 kWh/m2/yr) supports competitive solar PPA pricing.
- Option for on-site photovoltaic capacity to partially self-supply and hedge against grid price volatility.
- The Italian grid carbon intensity is projected to decline from ~310 gCO2/kWh (2025) to ~146 gCO2/kWh (2030) under Italy's NECP targets [SRC-ED-016, SRC-ED-017]. A PPA with certified renewable electricity (Guarantees of Origin) would reduce the Scope 2 emission factor to near zero.

### 5.2 Value Chain Analysis

#### 5.2.1 Primary Activities

| Activity | Description | Value Creation |
|----------|-------------|----------------|
| **Inbound logistics** | Precursor procurement, maritime/land transport to Brindisi, warehouse management | EU-sourced where possible; reduced transport carbon vs Asian supply |
| **CAM production** | 7-step solid-state synthesis: dosing -> milling -> spray drying -> calcination -> jet milling -> classification -> packaging | Electrified production with DT-optimised quality; battery-grade LFP CAM |
| **Quality control** | In-line PAT + at-line laboratory analysis + DT-predicted quality disposition | Superior batch consistency; full CQA traceability |
| **Outbound logistics** | Packaged LFP CAM delivery to European cell manufacturers via road/rail | Short supply chain to Southern/Central European customers |
| **Customer service** | Technical support for cell integration; custom product specifications; Battery Passport data provision | Differentiated service vs commodity Chinese supply |

#### 5.2.2 Value Proposition

The FACE plant creates value across multiple dimensions:

- **Supply chain security**: EU-produced LFP CAM eliminates single-source dependency on China [CLM-001]. European cell manufacturers gain a domestic supply option resilient to Chinese export controls [CLM-002].
- **Carbon footprint advantage**: Electrified production with Italian grid electricity delivers a materially lower product carbon footprint than gas-fired Chinese production, increasingly important under Battery Regulation carbon footprint performance class requirements.
- **Quality consistency**: DT-driven process control delivers superior batch-to-batch consistency versus empirical Chinese production methods [CLM-007, CLM-013].
- **Traceability and compliance**: Full digital traceability from precursor receipt to product shipment, natively supporting Battery Passport and due diligence requirements.

#### 5.2.3 Market Drivers

- **EV growth**: European EV sales growing at ~25% CAGR; LFP chemistry gaining share in standard-range vehicles due to cost and safety advantages [SRC-015].
- **ESS demand**: Grid-scale energy storage deploying rapidly across Europe; LFP is the dominant chemistry for stationary storage (>2,000 cycle life).
- **Battery Regulation**: Carbon footprint declaration and performance class requirements create a market premium for low-carbon CAM.
- **NZIA**: EU policy actively promotes domestic manufacturing of clean-tech components.

---

## 6. Technical Assessment

### 6.1 Design Philosophy and Basic Engineering

The FACE plant is designed according to the following principles:

**Electrification-first**: All thermal processing is electric. No natural gas infrastructure is installed. The plant is designed for a 20+ year operational life during which the Italian grid progressively decarbonises [CLM-030]. This avoids capital investment in gas infrastructure that would become stranded assets within 5-7 years as carbon pricing (EU ETS) and grid decarbonisation render gas-fired processes uncompetitive.

**DT-integrated from design phase**: The digital twin is not a retrofit -- it is designed into the plant from inception. All equipment is specified with digital connectivity requirements (OPC-UA interfaces, sensor ports, data tags). The DT data architecture is established during detailed engineering and commissioned in parallel with physical equipment. This contrasts with typical brownfield DT deployments where data infrastructure must be overlaid on legacy equipment.

**Modular and scalable**: The plant is designed in production-line modules that can be replicated to increase capacity. Each module comprises one spray dryer train and one calcination kiln train with associated milling and packaging. Additional modules can be added to the same site using the same utility infrastructure. The DT framework is inherently modular -- each production line has its own DT instance, with a plant-level supervisory DT coordinating across lines.

**Quality-by-Design**: The ICH Q8-adapted QbD framework [CLM-013, SRC-028] is embedded in the plant design: CQA targets define product specifications, CPP ranges define the design space, PAT sensors are specified as integral equipment (not optional add-ons), and the control strategy is DT-driven model-predictive control rather than recipe-based PID.

### 6.2 Main Systems and Long Lead Items

| # | System | Equipment | Key Specification | Est. Lead Time | Supplier Type |
|---|--------|-----------|-------------------|----------------|---------------|
| 1 | Precursor dosing | Gravimetric loss-in-weight feeders | +/-0.1% accuracy; 3 independent feeders (FePO4, Li2CO3, glucose) | 3-4 months | EU (Schenck Process, K-Tron/Coperion) |
| 2 | Dispersion | High-shear mixing tank | [ASSUMPTION: XX m3 capacity]; stainless steel 316L; variable speed drive | 2-3 months | EU |
| 3 | Sand milling | Horizontal bead mill (sand mill) | [ASSUMPTION: XX L grinding chamber]; ZrO2 bead media 0.3-0.5 mm; water-cooled | 4-6 months | EU/Asia (NETZSCH, WAB) |
| 4 | Magnetic separation (pre-spray drying) | Electromagnetic demagnetiser | Ferromagnetic removal to <0.1 ppm Fe metallic | 2-3 months | EU (Eriez, Bunting) |
| 5 | Spray drying (ELECTRIFIED) | Co-current electric spray dryer with HTHP pre-heating | Inlet 200-250 C; outlet 90-120 C; electric resistance heaters (Kanthal Tubothal/SiC); [ASSUMPTION: XX kg/h water evaporation capacity] | 6-9 months (LONG LEAD) | EU (GEA, Buchi Industrial, SPX/Anhydro) |
| 6 | Calcination (ELECTRIFIED) | Electric roller hearth kiln | 650-700 C operating temperature; N2 atmosphere (pO2 <10 ppm); multi-zone PID + MPC control; 95% thermal efficiency [CLM-023] | 9-12 months (LONG LEAD) | EU (Kanthal/Sandvik heating elements; NGK Insulators or ONEJOON kiln) |
| 7 | Crucible system | Alumina or graphite-lined refractory crucibles + external rail transport | Heat-resistant; compatible with N2 atmosphere; automated loading/unloading | 3-4 months | EU |
| 8 | Jet milling | Compressed gas jet mill (air or N2 jet) | Target D50 1-3 um; [ASSUMPTION: XX kg/h capacity] | 3-4 months | EU (NETZSCH, Hosokawa Alpine) |
| 9 | Classification | Ultrasonic vibrating sieve | Cut-off 10-20 um; high-throughput continuous operation | 2-3 months | EU (Russell Finex, Sweco) |
| 10 | Magnetic separation (post-milling) | Electromagnetic dry powder separator | Ferromagnetic removal from dry LFP powder | 2-3 months | EU (Eriez, Bunting) |
| 11 | Automated packaging | N2-blanketed automated packaging line | [ASSUMPTION: XX kg/bag]; moisture barrier bags; lot number/traceability | 2-3 months | EU |
| 12 | N2 supply system | PSA generator and/or bulk liquid N2 storage | >99.99% purity; [ASSUMPTION: XX Nm3/h capacity] | 3-6 months | EU (Air Liquide, Linde, SOL) |
| 13 | DT infrastructure | Edge computing nodes, OPC-UA gateways, sensor network, fog/cloud servers | ISO 23247 compliant; <100 ms edge-to-fog latency; InfluxDB time-series DB | 3-6 months | EU (Siemens, Beckhoff, ABB for OPC-UA; Dell/HPE for compute) |
| 14 | PAT sensor suite | Raman probes, FBRM, laser diffraction, pyrometers, IR cameras, O2/CO2 analysers | See Section 6.8 sensor deployment table | 3-6 months | EU/USA (Endress+Hauser, Mettler Toledo, HORIBA, Malvern Panalytical) |

**Critical path items**: The electric roller hearth kiln (Item 6, 9-12 months lead time) and electric spray dryer (Item 5, 6-9 months) define the equipment procurement critical path. Early vendor engagement and order placement is essential for schedule compliance.

[ASSUMPTION: Specific equipment vendors, detailed technical specifications, budgetary quotes, and confirmed lead times must be obtained during the Front-End Engineering Design (FEED) phase. The above specifications are indicative based on industry benchmarks and publicly available vendor data.]

### 6.3 Operational Characteristics

[ASSUMPTION: The following operational parameters are preliminary estimates that must be validated during FEED. The operating schedule, production capacity, and ramp-up plan are subject to market demand assessment and financial modelling by the CFO team.]

| Parameter | Value | Basis |
|-----------|-------|-------|
| Operating schedule | [ASSUMPTION: Continuous operation (24/7, 3 shifts) or 5-day/2-shift pattern -- to be determined based on capacity target and demand schedule] | Industry standard for CAM production |
| Annual production capacity | [ASSUMPTION: XX,000 tonnes LFP CAM/year at nameplate. For reference, FREYR targets 30,000 t/yr [SRC-025]] | To be confirmed by market analysis |
| Batch size (calcination) | [ASSUMPTION: XX kg per crucible x XX crucibles per kiln run] | Depends on kiln dimensions and crucible configuration |
| Calcination cycle time | 6-12 hours dwell at 650-700 C, plus ramp-up (~2 h) and controlled cooling (~4 h) [SRC-011, CLM-020] | Based on published LFP synthesis literature |
| Spray drying throughput | [ASSUMPTION: XX kg/h water evaporation; XX t/h slurry feed] | Depends on spray dryer capacity selected |
| Milling throughput | [ASSUMPTION: XX t/h for sand mill; XX t/h for jet mill] | Depends on equipment sizing |
| Product yield | >95% lithium and iron-phosphorus recovery; primary losses from CO2/volatile evolution during calcination | Stoichiometric basis |
| Utility consumption | Electricity: ~3-6 kWh/kg LFP CAM [CLM-027]; N2: [ASSUMPTION]; Water: [ASSUMPTION: largely recycled] | NMC analog; to be validated |

**Ramp-up schedule**:

| Period | Capacity Utilisation | Focus |
|--------|---------------------|-------|
| M42-M48 (commissioning) | 0-25% | Equipment shakedown; DT model calibration; process parameter optimisation |
| M48-M54 (Year 1 H1) | 25-50% | Product qualification with customer samples; CQA statistical validation |
| M54-M60 (Year 1 H2) | 50-80% | Full production ramp-up; DT closed-loop MPC activation |
| M60+ (Year 2+) | 80-100% | Steady-state production; continuous DT-driven optimisation |

### 6.4 Scale-Up Considerations

#### 6.4.1 LFP Solid-State Synthesis

The solid-state synthesis route for LFP is industrially mature (TRL 7-9) and has been scaled to >10,000 t/yr by multiple Chinese producers [CLM-001, SRC-011]. The fundamental chemistry and process steps are well-understood, and the FACE process follows the established industrial route. Scale-up risks are therefore concentrated in the novel elements (electrification, DT integration) rather than the core synthesis chemistry.

#### 6.4.2 Electrified Calcination

Electric roller hearth kilns are the industry standard for NMC CAM calcination at temperatures up to 950 C [SRC-ED-010, SRC-ED-023]. LFP calcination at 650-700 C operates well within the proven temperature envelope. Kanthal/Sandvik supplies electric heating elements (SiC Globar, Tubothal metallic) rated to 1,100 C for battery material applications [SRC-ED-009]. NGK's HD series roller hearth kiln achieves 40%+ energy reduction versus conventional tunnel kilns [SRC-ED-023].

The primary scale-up consideration is thermal uniformity across the kiln cross-section at production throughput. Non-uniform temperature distribution could create hot spots (>700 C, promoting impurity phases Li3PO4 and Fe2P) or cold spots (<600 C, incomplete olivine crystallisation) [CLM-020]. Mitigation:
- Multi-zone PID temperature control with independent heating elements per zone
- DT-driven MPC optimisation of zone-by-zone temperature setpoints using CFD-calibrated models [SRC-ED-010]
- Pilot-scale trials at kiln vendor facility (M6-M12) to validate temperature uniformity before equipment purchase

#### 6.4.3 Electrified Spray Drying

Industrial electric spray dryers are commercially proven for ceramics and food processing at comparable throughputs and temperatures [SRC-ED-001, SRC-ED-009]. The integration of high-temperature heat pump (HTHP) pre-heating with electric resistance final heating is the novel element. HTHP technology at COP 3.04 (120 C) is commercially available [SRC-ED-004]; COP 3.6 at 200 C has been demonstrated in peer-reviewed thermodynamic analysis [SRC-ED-005] but requires emerging transcritical heat pump systems.

Scale-up mitigation: initial design uses proven electric resistance heating for all spray dryer thermal demand, with HTHP integration as a Phase 2 energy optimisation upgrade once commercial 200 C HTHP units become available.

#### 6.4.4 Digital Twin Scale-Up

The DT framework is designed with modular architecture: each production-line module has its own DT instance with local edge computing, connected to a plant-level supervisory DT via fog/cloud infrastructure. This architecture scales linearly with production capacity -- adding a production module adds a DT instance without requiring fundamental architectural changes.

The primary scale-up challenge is model calibration: physics-based models (CFD, PBM, reaction kinetics) developed from literature data and vendor test results must be recalibrated against production-scale data during commissioning [CLM-018]. The systematic model calibration protocol (M42-M48) and hybrid physics + ML approach provide the recalibration pathway.

### 6.5 Technology Readiness Assessment

| # | Component | Current TRL | Target TRL at EiO | Evidence for Current TRL | Advancement Pathway |
|---|-----------|-------------|-------------------|--------------------------|---------------------|
| T1 | LFP solid-state synthesis | 7-8 | 9 | Dominant industrial route globally; proven at >10,000 t/yr by Chinese producers [CLM-001, SRC-011] | Process qualification at Brindisi; product certification with cell manufacturers |
| T2 | Electrified spray drying (electric resistance) | 7 | 9 | Commercially available equipment for ceramics/food (GEA, Buchi Industrial); proven at equivalent temperatures [SRC-ED-001] | Integration with LFP precursor slurry; optimisation of drying parameters for LFP particle morphology |
| T3 | HTHP for spray drying | 5-6 | 7 | COP 3.04 at 120 C demonstrated [SRC-ED-004]; COP 3.6 at 200 C in simulation [SRC-ED-005]; not yet integrated with LFP process | Qualification of commercial HTHP unit; integration with spray dryer air heating system |
| T4 | Electric roller hearth kiln for calcination | 7 | 9 | Commercially available (NGK, ONEJOON) and validated for NMC CAM at higher temperatures [SRC-ED-009, SRC-ED-010, SRC-ED-023] | Validation with LFP-specific chemistry; atmosphere (N2/pO2 <10 ppm) qualification |
| T5 | DT for CAM synthesis | 3-4 | 6-7 | Individual physics-based models validated: ARTISTIC (electrode DT [SRC-004]), TwinHeat (furnace DT), Ma et al. (sintering model [SRC-014]); no integrated LFP CAM DT exists [CLM-005] | Model integration; sensor fusion; closed-loop MPC commissioning; industrial validation |
| T6 | ISO 23247 for powder manufacturing | 3 | 6 | Standard defined and validated for discrete manufacturing [SRC-007, SRC-009, SRC-010, CLM-008]; not applied to chemical powder processes | Extend standard to chemical/powder domain; validate data exchange; demonstrate real-time capability |
| T7 | PAT/QbD for LFP | 4 | 7 | Pharmaceutical PAT mature (ICH Q8-Q11); individual sensors proven; CQA-CPP mapping documented [SRC-DT-REPORT]; not demonstrated for LFP CAM | Formal CQA-CPP validation with production data; design space establishment; RTRT implementation |
| T8 | Integrated plant (all components) | 4 | 7 | Novel combination of T1-T7; no integrated electrified LFP CAM plant with DT exists globally | System integration; commissioning; performance validation |

The composite starting TRL of 4 (for the integrated system) reflects the Innovation Fund's definition: individual components are demonstrated in laboratory or relevant environment, but the integrated system has not been validated in an operational environment. The target TRL of 7-9 (component-dependent) represents validated system performance in an operational environment, achieved through the project's phased commissioning programme.

### 6.6 Process Flow Description

The following describes each of the seven process steps in technical detail. *See Figure 2 in the Word document for the annotated process flow diagram.*

#### Step 1: Raw Material Dosing and Dispersion

**Inputs**: Iron phosphate (FePO4, powder), lithium carbonate (Li2CO3, powder), glucose (C6H12O6, powder or solution), deionised water.

**Operation**: The three solid precursors are gravimetrically dosed from dedicated silos using loss-in-weight feeders (+/-0.1% accuracy) into a stirred dispersion tank filled with deionised water. The stoichiometric target is Li:Fe:P = 1.00:1.00:1.00 (molar), with a deliberate lithium excess of 2-5 mol% to compensate for lithium volatilisation during calcination [SRC-011]. Glucose loading is 5-15 wt% relative to total solid content, providing the carbon precursor for in-situ carbon coating during the calcination step [CLM-020]. The resulting aqueous slurry (30-45 wt% solids) is homogenised by high-shear mixing (typically 15-30 minutes).

**Key process parameters**: Li:Fe:P molar ratio (CPP); glucose wt% (CPP); slurry solid content (CPP); mixing time and speed.

**DT integration**: Loss-in-weight feeder data is logged in real-time via OPC-UA to the DT. The stoichiometry calculator validates the molar ratios against target specifications. Deviation triggers an automatic alert and dosing correction.

**Outputs**: Homogeneous aqueous slurry of LFP precursors + glucose.

#### Step 2: Sand Milling and Magnetic Particle Removal

**Inputs**: Precursor slurry from Step 1.

**Operation**: The slurry is pumped through a horizontal sand mill (bead mill) containing zirconia (ZrO2) grinding beads (0.3-0.5 mm diameter). The mill provides high-energy mixing and particle size reduction, achieving intimate contact between precursor particles and reducing D50 to <5 um. The milled slurry is recirculated until the target particle size is confirmed by at-line laser diffraction. Following milling, the slurry passes through an electromagnetic demagnetiser to remove ferromagnetic contaminants (primarily iron wear particles from mill internals and bead fragments). Magnetic contamination above 0.1 ppm Fe metallic is a critical defect -- ferromagnetic particles can cause internal short circuits in finished battery cells.

**Key process parameters**: Mill tip speed; bead loading; number of passes; residence time.

**DT integration**: FBRM (Focused Beam Reflectance Measurement) probe provides in-line chord length distribution at 2-second update rate. The DT's population balance model (PBM) predicts D50 evolution and estimates milling endpoint. Laser diffraction provides at-line validation.

**Outputs**: Finely milled slurry (D50 <5 um) with magnetic contaminants removed.

#### Step 3: Spray Drying (ELECTRIFIED)

**Inputs**: Milled slurry from Step 2; electrically heated process air.

**Operation**: The slurry is atomised (rotary atomiser or pressure nozzle) into a co-current spray dryer with electrically heated inlet air at 200-250 C. The outlet air temperature is controlled at 90-120 C. Water evaporates from the droplets, producing dry, free-flowing spherical secondary particles (typical D50 20-80 um for spray-dried granules) comprising intimately mixed LFP precursors with uniformly distributed glucose.

The spray dryer uses electric resistance heaters (Kanthal Tubothal or SiC elements, rated to 1,100 C [SRC-ED-009]) for inlet air heating. Electric heating provides +/-1 C temperature control precision versus +/-5-10 C for gas burners [SRC-ED-018], which directly improves batch-to-batch reproducibility of dried particle properties.

**HTHP integration (Phase 2)**: A high-temperature heat pump pre-heats the inlet air to 120-200 C (COP 3.04-3.6 [SRC-ED-004, SRC-ED-005]), with electric resistance providing the final temperature boost to 200-250 C. This reduces electricity consumption for spray drying by 30-50% compared to resistance-only heating. Initial plant design uses resistance heating only, with HTHP integration as a retrofit upgrade.

Specific thermal energy demand: ~0.70-1.10 kWh per kg of water evaporated, based on Italian ceramics industry data for comparable spray dryers [SRC-ED-021].

**Key process parameters**: Inlet temperature (CPP); outlet temperature (CPP); feed rate (CPP); atomiser speed (CPP); air flow rate.

**DT integration**: Temperature mapping via thermocouples and IR camera at dryer inlet/outlet; humidity sensor for outlet air moisture; product collection rate monitoring. The DT spray drying model predicts dried particle properties (D50, morphology, residual moisture) from current operating conditions and adjusts inlet temperature and feed rate via MPC.

**Outputs**: Dry, free-flowing precursor powder (spherical granules, residual moisture <2 wt%).

#### Step 4: Calcination (ELECTRIFIED -- Key Innovation Step)

**Inputs**: Dried precursor powder from Step 3; nitrogen gas (>99.99% purity).

**Operation**: The dried precursor powder is loaded into refractory crucibles (alumina or graphite-lined) and introduced into the electric roller hearth kiln via an automated external rail system. The kiln operates under flowing nitrogen atmosphere (pO2 <10 ppm) with a multi-zone temperature profile:

| Temperature Zone | Range | Duration | Chemical Process | Activation Energy |
|-----------------|-------|----------|-----------------|-------------------|
| Ramp-up | RT to 200 C | ~1 h | Moisture removal | -- |
| Decomposition | 200-400 C | ~2 h | Glucose pyrolysis; amorphous carbon formation | 65-90 kJ/mol |
| Carbothermal reduction | 400-550 C | ~2 h | Fe3+ reduced to Fe2+ by carbon; intermediate phases form (Li3Fe2(PO4)3, Fe2O3) | 90-120 kJ/mol |
| Olivine crystallisation | 550-700 C | 4-8 h (main dwell) | Nucleation and growth of LiFePO4 olivine phase (Jander/Avrami kinetics) | 120-180 kJ/mol |
| Carbon coating consolidation | 600-700 C | Concurrent with above | Residual carbon forms 2-5 nm conductive coating on LFP particles | -- |
| Controlled cooling | 700 C to RT | ~4 h | Slow cooling to avoid thermal stress cracking; maintained under N2 | -- |

[CLM-020, SRC-011, SRC-DT-REPORT]

The electric roller hearth kiln achieves 95% thermal efficiency versus 25-60% for gas-fired kilns [CLM-023, SRC-ED-009]. Multi-zone independent PID temperature control with Kanthal SiC or Tubothal heating elements enables precise temperature profile shaping compatible with DT-driven MPC optimisation. The absence of combustion gases simplifies atmosphere control -- in a gas-fired kiln, combustion products (H2O, CO2, trace O2) contaminate the N2 atmosphere, making strict pO2 control more challenging.

**Critical process control requirements**:
- pO2 must remain <10 ppm throughout calcination to prevent Fe2+ surface oxidation to Fe3+, which degrades electronic conductivity and electrochemical capacity
- Temperature must not exceed ~750 C to avoid formation of impurity phases (Li3PO4, Fe2P)
- Cooling rate must be controlled to prevent thermal stress-induced particle cracking

**Key process parameters**: Temperature profile (CPP -- zone-by-zone setpoints); N2 flow rate (CPP); pO2 level (CPP); dwell time at peak temperature (CPP); cooling rate (CPP).

**DT integration**: This is the highest-value DT intervention point. Sensor suite includes: Type K/S thermocouples (contact, +/-1.5 C), ratio pyrometers (non-contact, +/-0.5%), IR cameras (full-field 2D thermal mapping), zirconia O2 sensors (<10 ppm resolution), NDIR analysers for CO2/CO/CH4 evolved gas analysis [SRC-DT-REPORT]. The DT core runs a CFD-calibrated thermal model combined with multi-step reaction kinetics (Jander/Avrami) to predict olivine conversion, impurity formation, and carbon coating quality in real-time. MPC optimises the temperature profile to minimise energy consumption while maintaining CQA targets within the validated design space.

Post-calcination at-line analysis: Raman spectroscopy (olivine phase at 950 cm-1, carbon D/G ratio, impurity phases), XRD (phase purity by Rietveld refinement), XRF (elemental composition verification).

**Outputs**: Calcined LFP/C powder with target phase purity >98% olivine, carbon content 1.5-3.0 wt%.

#### Step 5: Jet Milling

**Inputs**: Calcined LFP/C powder from Step 4.

**Operation**: The calcined product consists of sintered agglomerates that must be de-agglomerated to the final target particle size (D50 1-3 um). A compressed gas jet mill (nitrogen or air) achieves high-velocity interparticle collisions that break agglomerates while preserving the olivine crystal structure and carbon coating integrity. The built-in classifier ensures only particles below the target D90 exit the mill.

**Key process parameters**: Grinding gas pressure (CPP); classifier speed (CPP); feed rate.

**DT integration**: The DT's DEM (Discrete Element Method) model predicts particle breakage kinetics and final PSD from milling energy and classifier settings. FBRM provides in-line chord length distribution; laser diffraction provides at-line D10/D50/D90 validation.

**Outputs**: De-agglomerated LFP/C powder (D50 1-3 um).

#### Step 6: Ultrasonic Sieving and Demagnetisation

**Inputs**: Milled LFP/C powder from Step 5.

**Operation**: The powder passes through an ultrasonic vibrating sieve (cut-off 10-20 um) to remove oversized particles and any residual agglomerates. Subsequently, an electromagnetic dry powder separator removes ferromagnetic contaminants potentially introduced during milling. The final D50, span, and magnetic contamination level are verified by at-line measurements.

**Key process parameters**: Sieve aperture; ultrasonic frequency/amplitude; magnetic field strength.

**DT integration**: At-line laser diffraction and magnetic susceptibility measurements feed into the DT for batch disposition decision.

**Outputs**: Classified, demagnetised LFP/C powder meeting final PSD and purity specifications.

#### Step 7: Automated Packaging

**Inputs**: Qualified LFP/C powder from Step 6.

**Operation**: Product is automatically weighed and packaged under nitrogen atmosphere (N2 blanketing) in multi-layer moisture-barrier bags. Each bag is sealed, labelled with lot number and QR code, and palletised. Full batch traceability is maintained -- the DT records all process parameters, sensor data, and quality test results against the lot number, forming the basis for Battery Passport data.

**Key process parameters**: Package weight; N2 blanket purity; seal integrity.

**DT integration**: Final batch quality report generated automatically. DT compares all CQA measurements against specifications and issues pass/fail disposition. All data archived in time-series database for Battery Passport compliance.

**Outputs**: Packaged, qualified battery-grade LiFePO4/C cathode active material.

### 6.7 Mass and Energy Balances

#### 6.7.1 Mass Balance (per tonne of LFP CAM product)

The solid-state synthesis reaction can be summarised as:

LiFePO4 formation: Li2CO3 + 2 FePO4 + C6H12O6 -> 2 LiFePO4/C + CO2 + H2O (simplified)

| Input | Quantity (per t LFP CAM) | Notes |
|-------|--------------------------|-------|
| FePO4 (iron phosphate) | ~1,000-1,050 kg | Stoichiometric + 2-5% excess to ensure complete reaction |
| Li2CO3 (lithium carbonate) | ~240-260 kg | Stoichiometric + 2-5% Li excess to compensate for volatilisation |
| Glucose (C6H12O6) | 50-150 kg | 5-15 wt% of total solids; carbon source for in-situ coating |
| Deionised water | [ASSUMPTION: ~1,500-3,000 L] | Slurry medium; >90% recovered from spray dryer condensate |
| Nitrogen gas | [ASSUMPTION: XX Nm3] | Calcination atmosphere; partially recycled via closed-loop scrubbing |
| Electricity | ~3,000-6,000 kWh | Total process energy [CLM-027, analog from NMC ~4 kWh/kg] |

| Output | Quantity (per t LFP CAM) | Notes |
|--------|--------------------------|-------|
| LiFePO4/C product | 1,000 kg | Battery-grade, packaged |
| CO2 (from Li2CO3 decomposition) | ~280 kg | Process CO2; stoichiometric from carbonate |
| CO2/H2O (from glucose pyrolysis) | ~50-100 kg | Volatile products captured in off-gas treatment |
| Water vapour (from spray drying) | [ASSUMPTION: ~1,500-3,000 kg] | Recovered from spray dryer condensate |
| Off-spec product | <50 kg (<5%) | Recycled to precursor stage |
| Spent grinding media | Negligible (replaced periodically) | ZrO2 beads; metal recycling |

Product yield: >95% (Li and Fe-P basis), with primary mass losses from CO2 evolution during carbonate decomposition and volatile organic evolution during glucose pyrolysis.

#### 6.7.2 Energy Balance (per tonne of LFP CAM product)

| Process Step | Gas-Fired Reference (kWh_thermal) | Electrified (FACE) (kWh_electric) | Source |
|-------------|-----------------------------------|-----------------------------------|--------|
| Spray drying | [ASSUMPTION: ~800-1,200 kWh_th] | ~400-800 kWh_e (resistance) or ~220-330 kWh_e (with HTHP at COP 3.6) | [SRC-ED-001, SRC-ED-005, SRC-ED-021] |
| Calcination | [ASSUMPTION: ~1,500-2,500 kWh_th at 25-60% gas efficiency] | ~700-1,200 kWh_e (at 95% electric efficiency) | [CLM-023, SRC-ED-009, SRC-ED-010] |
| Milling (sand + jet) | ~200-400 kWh_e | ~200-400 kWh_e | Same (electric in both cases) |
| Auxiliaries (mixing, conveying, packaging, HVAC, water treatment) | ~200-400 kWh | ~200-400 kWh_e | Same |
| **Total** | **~2,700-4,500 kWh/t** (gas thermal + electric) | **~1,500-2,800 kWh_e/t** (resistance only) or **~1,300-2,300 kWh_e/t** (with HTHP) | [CLM-027] |

[ASSUMPTION: These energy estimates are derived from NMC CAM analog data (~4 kWh/kg = 4,000 kWh/t [SRC-ED-011]) and electrification efficiency ratios. LFP-specific industrial energy data does not exist in published literature [CLM-028]. The FACE project will generate the first primary LFP CAM energy data. The engineering team must validate these estimates with equipment vendor data during FEED.]

The electrified process achieves lower total energy consumption than the gas-fired reference because:
1. Electric kilns operate at 95% thermal efficiency versus 25-60% for gas [CLM-023]
2. Electric heating eliminates combustion gas losses and atmosphere contamination
3. HTHP provides 3.0-3.6x thermodynamic advantage for spray drying pre-heating [SRC-ED-004, SRC-ED-005]

### 6.8 Digital Twin Architecture

The FACE digital twin implements the ISO 23247:2021 four-layer manufacturing digital twin architecture [CLM-008, SRC-007, SRC-008]. This section describes each layer in detail.

#### 6.8.1 Layer 1 -- Observable Manufacturing Element (OME)

Layer 1 comprises the physical plant assets and their associated instrumentation. Each major equipment unit is assigned a unique asset identifier within the DT framework.

**Equipment inventory**:

| Asset ID | Equipment | Location | Key Instruments |
|----------|-----------|----------|-----------------|
| OME-001 | Gravimetric feeders (x3) | Step 1 - Dosing | Load cells, flow meters |
| OME-002 | Dispersion tank | Step 1 - Mixing | Level, temperature, viscosity |
| OME-003 | Sand mill | Step 2 - Milling | Power draw, temperature, FBRM probe |
| OME-004 | Demagnetiser (pre-spray) | Step 2 - Mag separation | Magnetic field strength, throughput |
| OME-005 | Electric spray dryer | Step 3 - Drying | Inlet/outlet T, humidity, product rate |
| OME-006 | Electric roller hearth kiln | Step 4 - Calcination | Multi-zone T, pO2, CO2/CO, IR camera |
| OME-007 | Jet mill | Step 5 - Milling | Air pressure, classifier speed, power |
| OME-008 | Ultrasonic sieve | Step 6 - Classification | Vibration frequency, throughput |
| OME-009 | Demagnetiser (post-mill) | Step 6 - Mag separation | Magnetic field strength |
| OME-010 | Packaging line | Step 7 - Packaging | Weight, N2 purity, seal integrity |

#### 6.8.2 Layer 2 -- Data Collection and Device Control (DCDC)

Layer 2 manages all physical-digital data exchange through a hierarchical communication architecture:

**Communication architecture**:
- **Field level**: Sensors and actuators communicate via industrial fieldbus (PROFINET, EtherNet/IP) to local PLCs
- **Edge level**: Edge computing nodes (industrial PCs) aggregate data from PLCs via OPC-UA, perform data pre-processing (filtering, feature extraction, anomaly flagging), and publish to the fog layer via MQTT
- **Fog level**: On-site fog servers run time-critical DT models (surrogate inference <1 second) and MPC controllers
- **Cloud level**: Off-site or on-site cloud infrastructure handles batch archival, model retraining, reporting, and long-term analytics

**Target latencies**: Field-to-edge <10 ms; edge-to-fog <100 ms; fog-to-cloud <1 second.

**PAT sensor deployment table**:

| # | Measurement | Technology | Location | Frequency | Primary CQA Target | Inline/Atline |
|---|-------------|------------|----------|-----------|-------------------|---------------|
| S1 | Temperature (contact) | Type K thermocouple (+/-1.5 C) | Calcination kiln -- multiple zones | 1-10 Hz | Phase purity, carbon quality | In-line |
| S2 | Temperature (non-contact) | Ratio pyrometer (+/-0.5%) | Calcination kiln exit | 1-10 Hz | Phase purity | In-line |
| S3 | Temperature field (2D) | IR camera | Kiln exit, spray dryer | 10 Hz | Temperature uniformity | In-line |
| S4 | Particle size (slurry) | FBRM probe (0.5-2000 um) | Sand mill outlet | 2 sec | D50 (milled slurry) | In-line |
| S5 | Particle size (powder) | Laser diffraction | Post-jet mill (at-line) | 60 sec | D50, D10, D90 | At-line |
| S6 | Phase composition | In-line Raman probe (950 cm-1 olivine) | Post-calcination sampling | 30-60 sec | Phase purity, carbon D/G | At-line |
| S7 | Atmosphere O2 | Zirconia O2 sensor (<10 ppm) | Calcination kiln atmosphere | 1-5 sec | Fe2+/Fe3+ ratio | In-line |
| S8 | Evolved gas | NDIR (CO2, CO, CH4) | Calcination kiln exhaust | 1-5 sec | Reaction progress | In-line |
| S9 | Elemental composition | XRF | Post-milling sampling | 5 min | Li:Fe:P stoichiometry | At-line |
| S10 | Moisture | NIR probe | Spray dryer product, packaging | Continuous | Moisture <200 ppm | In-line |
| S11 | Magnetic contamination | Magnetic susceptibility meter | Post-demagnetisation | Per batch | Ferromagnetic particles | At-line |

#### 6.8.3 Layer 3 -- Digital Twin Core Entity

Layer 3 is the computational engine of the DT, comprising physics-based models, data-driven models, and the data management infrastructure.

**Multi-scale model hierarchy**:

| Scale | Method | Software | Application | Execution Mode |
|-------|--------|----------|-------------|----------------|
| Atomistic | DFT (Density Functional Theory) | VASP / Quantum ESPRESSO | LFP olivine formation energetics, defect energies, Li+ migration barriers | Offline (hours/run); populates material property database |
| Molecular | Classical MD | LAMMPS | Carbon coating pyrolysis mechanisms, surface adsorption | Offline (hours/run); calibrates mesoscale models |
| Mesoscale | Phase-field / Kinetic Monte Carlo | Custom / MOOSE | Nucleation and grain growth kinetics during calcination | Offline (minutes-hours/run); generates kinetic parameters |
| Continuum | CFD + PBM + reaction kinetics | COMSOL / OpenFOAM + custom PBM | Calcination kiln heat/mass transfer; spray dryer droplet drying; Jander/Avrami reaction kinetics | Offline for training data; surrogate (PINN) for real-time |
| Equipment | DEM (Discrete Element Method) | EDEM / LIGGGHTS | Jet mill particle breakage and classification | Offline; lookup tables for real-time |
| Plant | Flowsheet simulation | Aspen Plus / gPROMS | Mass/energy balance; throughput optimisation; batch scheduling | Batch-level (minutes) |

**Physics-Informed Neural Networks (PINNs)**: The key to real-time capability. High-fidelity CFD and PBM simulations are computationally expensive (hours per calcination cycle simulation). PINNs are trained on libraries of pre-computed simulation results to provide surrogate predictions with <1 second inference time. The PINN architecture encodes the governing physics (energy balance, reaction kinetics) as constraints in the loss function, ensuring predictions remain physically consistent even for extrapolation beyond the training data range. This approach is validated by TwinHeat (MINES Paris), which achieved <1 C prediction accuracy for furnace temperature fields using neural network surrogates trained on CFD data [CLM-016].

**Data pipeline**:
- Time-series sensor data: InfluxDB (high-frequency ingestion, retention policies, downsampling)
- Batch archival: HDF5 files per batch (complete process trajectory + quality data)
- Data lake: Delta Lake on cloud storage for long-term analytics and model retraining
- Model registry: MLflow for surrogate model versioning, deployment, and performance tracking

**ML pipelines**:
- Anomaly detection: Autoencoder-based (following Fraunhofer DiBaZ approach [CLM-017]) for detecting out-of-distribution process behaviour
- Multivariate SPC: PCA/PLS-based process monitoring with T2 and SPE control charts
- Predictive quality: Gradient boosting / neural network models correlating CPP trajectories to final CQAs
- Bayesian optimisation: For iterative process optimisation during ramp-up (following ARTISTIC approach [SRC-004])

#### 6.8.4 Layer 4 -- User Entity

Layer 4 provides the human-machine interface:

- **Real-time dashboards** (Grafana): Process state visualisation, CQA predictions with confidence intervals, control action log, equipment health indicators
- **MPC operator interface**: Model-predictive control for calcination temperature profile optimisation, spray drying parameter adjustment, milling energy control. The MPC operates on a receding-horizon optimisation minimising a cost function combining CQA deviation, energy consumption, and throughput.
- **Batch quality reports**: Automatic generation at batch completion with CQA measurements vs specifications, process trajectory analysis, DT-predicted vs actual comparison, and pass/fail disposition
- **Predictive maintenance**: Equipment health indicators derived from DT analysis of sensor trends (heating element degradation, sensor drift, mechanical wear). Maintenance scheduling recommendations based on condition rather than calendar.
- **Battery Passport interface**: Structured data export compliant with Battery Regulation 2023/1542 requirements, providing full material and process traceability per lot.

---

## 7. Expected Project Output

### 7.1 Production Volume

[ASSUMPTION: The target annual production capacity must be confirmed by the project team based on market demand assessment and financial modelling. For reference, the comparable FREYR project targets 30,000 t/yr [SRC-025]. Capacity at FACE is expected to be in the range of XX,000 t/yr LFP CAM, achievable through installation of XX production-line modules.]

**Ramp-up trajectory**:

| Year | Capacity Utilisation | Estimated Output |
|------|---------------------|------------------|
| Year 1 (post-EiO) | 50% average | [ASSUMPTION: XX,000 t] |
| Year 2 | 80% | [ASSUMPTION: XX,000 t] |
| Year 3+ | 100% (nameplate) | [ASSUMPTION: XX,000 t/yr] |

### 7.2 Product Quality

The FACE plant produces battery-grade LiFePO4/C powder meeting the following CQA specifications:

| CQA | Target | Min/Max Specification | Test Method | Test Standard |
|-----|--------|----------------------|-------------|---------------|
| D50 particle size | 1-3 um | +/- 0.5 um | Laser diffraction | ISO 13320 |
| D10 | >0.5 um | Min 0.3 um | Laser diffraction | ISO 13320 |
| D90 | <10 um | Max 15 um | Laser diffraction | ISO 13320 |
| BET surface area | 12-18 m2/g | +/- 3 m2/g | N2 adsorption | ISO 9277 |
| Tap density | 1.0-1.4 g/cm3 | >1.0 g/cm3 | Standardised tapping | ASTM B527 |
| Phase purity (olivine) | >98% LiFePO4 | Min 97% | XRD Rietveld refinement | ISO 16700 (adapted) |
| Fe2+/Fe3+ ratio | >0.95 | Min 0.90 | Mossbauer spectroscopy / XPS | -- |
| Carbon content | 1.5-3.0 wt% | +/- 0.5 wt% | TGA / combustion analysis | -- |
| Carbon D/G ratio (Raman) | 0.8-1.2 | Range | Raman spectroscopy | -- |
| Discharge capacity (C/10) | >155 mAh/g | Min 150 mAh/g | Half-cell electrochemical | IEC 62660-1 (adapted) |
| Rate capability (5C) | >120 mAh/g | Min 100 mAh/g | Half-cell electrochemical | IEC 62660-1 (adapted) |
| Moisture | <200 ppm | Max 500 ppm | Karl Fischer titration | ASTM E203 |
| Magnetic contamination (Fe metallic) | <0.1 ppm | Max 0.5 ppm | Magnetic susceptibility | -- |

These specifications are competitive with Tier-1 Chinese LFP CAM (CATL, BYD) and aligned with the requirements published by European cell manufacturers for LFP cathode qualification.

### 7.3 Turndown, Availability, and Reliability

| Parameter | Target | Basis |
|-----------|--------|-------|
| Minimum turndown | 25% of nameplate capacity | Minimum batch size for spray dryer and kiln operation |
| Plant availability | >90% (Year 2+) | Industry benchmark for continuous chemical process plants |
| On-stream factor | >85% (Year 2+) | Accounting for planned maintenance, batch changeover, QC holds |
| Mean time between failures (MTBF) | [ASSUMPTION: To be established from vendor MTBF data for critical equipment (kiln, spray dryer)] | Vendor specifications |
| Mean time to repair (MTTR) | <8 hours for non-critical failures; <48 hours for critical equipment | Based on spare parts inventory and maintenance team capability |

### 7.4 Maintenance Strategy

The FACE plant implements a **DT-enabled predictive maintenance** strategy that progresses from time-based to condition-based to predictive maintenance over the first two years of operation:

**Year 1**: Time-based maintenance per vendor recommendations, supplemented by DT monitoring of equipment health indicators (heating element resistance trends, sensor calibration drift, motor vibration signatures, bearing temperature).

**Year 2+**: Transition to condition-based and predictive maintenance as the DT accumulates sufficient operational data to train equipment degradation models. Key predictive maintenance targets:
- Heating element degradation in calcination kiln (resistance increase → temperature non-uniformity → predict replacement timing)
- Sensor drift (particularly zirconia O2 sensors at high temperature) → automated recalibration scheduling
- Grinding media wear in sand mill → predict replacement interval from particle size evolution trends
- Spray dryer nozzle wear → predict atomisation degradation from product particle size trends

DT-enabled predictive maintenance is projected to reduce unplanned downtime by 20-50% versus calendar-based maintenance [CLM-007].

### 7.5 GHG Emission Avoidance

The Innovation Fund GHG avoidance calculation compares the FACE electrified plant against a gas-fired reference case (Asian benchmark technology). The key parameters are:

| Parameter | Gas-Fired Reference | FACE (Electrified) | Source |
|-----------|--------------------|--------------------|--------|
| Process energy source | Natural gas (spray drying + calcination) | Electricity (Italian grid + PPA) | Design specification |
| Thermal efficiency (calcination) | 25-60% | 95% | [CLM-023, SRC-ED-009] |
| Grid carbon intensity | N/A (gas: ~0.2 kgCO2/kWh_th) | Italy 2030: ~146 gCO2/kWh_e [SRC-ED-017]; PPA: ~0 gCO2/kWh_e | [SRC-ED-016, SRC-ED-017] |
| Process CO2 (from Li2CO3 decomposition) | ~280 kgCO2/t LFP (same for both) | ~280 kgCO2/t LFP (same for both) | Stoichiometric |
| Total GHG per t LFP CAM | [ASSUMPTION: To be calculated in GHG calculator by CFO team] | [ASSUMPTION: To be calculated] | Innovation Fund GHG methodology |
| Relative GHG avoidance | Reference case | Target: >=50% [CLM-026] | |

**GHG trajectory**:

| Scenario | Grid Intensity | Relative GHG Avoidance vs Gas-Fired |
|----------|---------------|--------------------------------------|
| 2028 (EiO, grid only) | ~180 gCO2/kWh | ~30-40% |
| 2028 (EiO, with PPA) | ~50 gCO2/kWh (blended) | ~55-65% |
| 2030 (NECP target) | ~146 gCO2/kWh | 55-70% [CLM-026] |
| 2035 (G7 commitment) | ~30-60 gCO2/kWh | 80-90% [CLM-026] |

[ASSUMPTION: The detailed GHG avoidance calculation, including all Scope 1, 2, and 3 emissions, transport, and upstream supply chain emissions, is the responsibility of the CFO team using the Innovation Fund GHG calculator tool. The above figures are directional estimates based on analog data. The final GHG calculation must use the specific production capacity, energy consumption data validated by equipment vendors, and the Innovation Fund's prescribed methodology.]

---

## 8. Techno-Economic Analysis

**[CFO TEAM TO COMPLETE THIS SECTION]**

This section requires the following content to be developed by the CFO/finance team in coordination with the technical team:

### 8.1 CAPEX Estimation

Required:
- Total CAPEX breakdown by category (equipment, civil works, utilities, DT infrastructure, engineering, contingency)
- AACE cost estimation class (target Class 3 or better for Innovation Fund)
- Quotes from technology suppliers (kiln vendor, spray dryer vendor, DT platform vendor) where available
- Comparison with gas-fired alternative CAPEX (to demonstrate the CAPEX premium for electrification and DT that the Innovation Fund grant addresses)
- Currency and base date for cost estimates

### 8.2 OPEX Estimation

Required:
- Annual OPEX breakdown: raw materials (FePO4, Li2CO3, glucose), electricity, N2, water, labour, maintenance, insurance, DT operating costs
- Unit production cost (EUR/t LFP CAM and EUR/kg)
- Sensitivity analysis to key cost drivers (lithium price +/-50%, electricity price +/-30%, production volume +/-25%)
- Comparison with estimated Chinese production cost (benchmark)

### 8.3 Technology Supplier Quotes

Required:
- Budgetary quotes or LOIs from: calcination kiln vendor (NGK, ONEJOON, or equivalent); spray dryer vendor (GEA, Buchi Industrial, or equivalent); DT platform/integration vendor
- These quotes should be attached as confidential annexes if available

### 8.4 Comparison with Gas-Fired Alternative

Required:
- Side-by-side CAPEX/OPEX comparison: electrified plant (FACE) vs hypothetical gas-fired plant (same capacity)
- TCO analysis over 20-year plant life including: gas price volatility, EU ETS carbon price trajectory, avoided stranded asset costs
- Demonstration that Innovation Fund grant is necessary to close the CAPEX gap between electrified and gas-fired alternatives

### 8.5 Environmental and Socio-Economic Impacts

Required:
- Job creation (direct and indirect): construction phase and operational phase
- Tax revenue contribution to Comune di Brindisi and Regione Puglia
- Training and skills development programme for local workforce
- Health and safety assessment (no combustion-related workplace emissions; reduced NOx/SOx exposure)
- Contribution to Puglia convergence region economic development

### 8.6 Tabular Summary

Required: Summary table consistent with the Business Plan annex, showing:

| Parameter | Value | Unit |
|-----------|-------|------|
| Total CAPEX | [CFO to complete] | EUR million |
| Annual OPEX (at nameplate) | [CFO to complete] | EUR million/year |
| Production capacity | [CFO to complete] | t LFP CAM/year |
| Unit cost | [CFO to complete] | EUR/kg LFP CAM |
| Innovation Fund grant requested | [CFO to complete] | EUR million |
| Co-funding rate | 60% | % of relevant costs |
| NPV (20-year) | [CFO to complete] | EUR million |
| IRR | [CFO to complete] | % |
| Payback period | [CFO to complete] | Years |

---

## 9. Risk Analysis and Management

### 9.1 Technical Risks

| # | Risk Description | Likelihood | Impact | Risk Level | Ownership | Mitigation Measures |
|---|-----------------|------------|--------|------------|-----------|---------------------|
| TR1 | **Calcination scale-up**: Difficulty achieving target CQAs (phase purity >98%, D50 1-3 um) at production scale due to thermal non-uniformity in larger kiln | Medium | High | **High** | FIB (Technical Director) | (a) Pilot-scale trials at kiln vendor facility (M6-M12) to validate temperature uniformity and product quality before equipment purchase; (b) phased production ramp-up from 25% to 100% nameplate capacity (M48-M54); (c) DT-driven furnace zone optimisation using CFD-calibrated models [CLM-016, SRC-ED-010]; (d) multi-zone independent PID + MPC control |
| TR2 | **DT model accuracy at production scale**: Physics-based models calibrated on literature data and vendor test data may not accurately predict production-scale behaviour | Medium | Medium | **Medium** | FIB (DT Lead) | (a) Systematic model calibration protocol using commissioning batch data (M42-M48); (b) hybrid physics + ML approach where data-driven corrections compensate for model discrepancies [CLM-018]; (c) conservative initial operating setpoints with gradual DT-guided optimisation; (d) independent model validation by academic partner |
| TR3 | **Sensor degradation at high temperature**: Raman probes, thermocouples, and O2 sensors operating at >600 C may experience fouling, drift, or failure during extended campaigns | Medium | Medium | **Medium** | FIB (Process Engineering) | (a) Redundant sensing architecture: multiple sensor types per critical measurement (thermocouples + pyrometers + IR cameras for temperature) [CLM-019]; (b) scheduled preventive maintenance with sensor replacement intervals; (c) virtual sensors (ML-inferred predictions from correlated measurements) as backup |
| TR4 | **Spray drying optimisation for LFP**: Electric spray dryer parameters (inlet T, feed rate, atomiser speed) may require extensive optimisation to achieve target particle morphology for LFP precursor | Low | Medium | **Low-Medium** | FIB (Process Engineering) | (a) Spray drying trials at vendor test facility using LFP precursor slurry (M12-M18); (b) DT-based DoE to efficiently explore parameter space; (c) electric heating enables precise temperature control (+/-1 C) aiding reproducibility [SRC-ED-018] |
| TR5 | **Product quality consistency across batches**: Batch-to-batch variability in CQAs may exceed customer specifications during early production | Medium | High | **High** | FIB (Quality Director) | (a) DT-driven MPC to maintain operation within validated design space; (b) Bayesian optimisation for iterative process improvement [SRC-004]; (c) statistical process capability monitoring (target Cpk > 1.33); (d) conservative production ramp-up with progressive quality qualification |
| TR6 | **IP/licensing risk**: Third-party patents (LG Chem EP2360117B1, AspenTech EP4222563A4) may constrain product specifications or DT platform choice | Low | Medium | **Low** | FIB (Legal) | (a) Freedom-to-operate assessment completed -- no blocking patents identified [CLM-014]; (b) LG Chem patent expires ~2029 -- design product specifications outside claim scope; (c) if AspenTech platform used, licence included; (d) proactive patent filing for novel DT-electrification combination |
| TR7 | **Precursor quality variability**: Incoming FePO4 and Li2CO3 quality variation from different suppliers may affect process stability and product quality | Low | Medium | **Low-Medium** | FIB (Quality / Procurement) | (a) Incoming raw material QC testing (XRF, PSD, moisture) before use; (b) supplier qualification programme with CQA-relevant specifications; (c) DT adaptive control adjusts process parameters based on measured precursor properties |
| TR8 | **N2 atmosphere control under electric heating**: Maintaining pO2 <10 ppm in electric roller hearth kiln requires careful sealing and N2 flow design | Low | High | **Medium** | FIB (Process Engineering) | (a) Kiln specification includes sealed enclosure with N2 purge design; (b) electric kilns for NMC operate at even stricter atmosphere requirements [SRC-ED-010]; (c) continuous pO2 monitoring with automatic N2 flow increase on deviation; (d) DT monitors atmosphere trends and predicts seal degradation |
| TR9 | **Grid reliability**: Power grid interruption during calcination could result in batch loss (incomplete reaction, thermal shock to crucibles/product) | Low | High | **Medium** | Eni (Site Operations) | (a) Uninterruptible power supply (UPS) for critical control systems; (b) controlled shutdown procedure activated within 30 seconds of grid failure; (c) on-site emergency generator for orderly plant shutdown (not for full production continuation); (d) evaluate battery energy storage for short-duration ride-through |
| TR10 | **Equipment integration**: Integration of DT infrastructure (sensors, OPC-UA gateways, edge computing) with production equipment from multiple vendors may present interoperability challenges | Medium | Low | **Low-Medium** | FIB (DT Lead / Automation) | (a) OPC-UA as mandatory communication standard in all equipment specifications; (b) Factory Acceptance Testing (FAT) with DT connectivity verification; (c) dedicated integration testing phase (M36-M42) before production commissioning; (d) industrial integration partner (e.g., Siemens, ABB) for system integration |

### 9.2 Operational Risks

| # | Risk Description | Likelihood | Impact | Risk Level | Ownership | Mitigation Measures |
|---|-----------------|------------|--------|------------|-----------|---------------------|
| OR1 | **Construction timeline delay**: Civil works, equipment delivery, or installation exceeds schedule | Medium | Medium | **Medium** | FIB (Project Manager) | (a) Critical path scheduling with early procurement of long-lead items (kiln M0+3, spray dryer M0+6); (b) brownfield site reduces civil works scope; (c) 3-month schedule buffer in overall timeline; (d) experienced EPC contractor selection |
| OR2 | **Permitting delays**: VIA or AIA permitting exceeds expected timeline | Medium | Medium | **Medium** | Eni (Regulatory Affairs) | (a) Early engagement with Regione Puglia and MASE; (b) leverage Eni's established Brindisi regulatory relationships; (c) experienced environmental permitting consultants; (d) 3-month schedule buffer; (e) electrified process simplifies air emissions assessment |
| OR3 | **Workforce recruitment**: Difficulty recruiting qualified process engineers, DT specialists, and production operators in Brindisi | Medium | Medium | **Medium** | FIB (HR Director) | (a) Recruitment campaign starting M0; (b) partnerships with Politecnico di Bari and Universita del Salento for graduate recruitment; (c) training programme for existing FIB employees to cross-skill into CAM production; (d) competitive salary packages for DT specialists |
| OR4 | **Commissioning challenges**: Extended commissioning period due to integration complexity of electrified equipment + DT | Medium | Medium | **Medium** | FIB (Commissioning Manager) | (a) Phased commissioning: equipment mechanical completion -> cold commissioning -> hot commissioning with non-critical material -> production trials with actual precursors; (b) DT commissioning in parallel (digital commissioning before physical); (c) vendor technical support during commissioning |
| OR5 | **Market timing**: Delay in European EV/ESS market growth or LFP chemistry adoption may reduce demand below plant capacity | Low | Medium | **Low-Medium** | FIB (Commercial Director) | (a) Growing EU LFP demand driven by EV and ESS growth [SRC-015]; (b) Battery Regulation carbon footprint requirements create preference for EU-manufactured CAM; (c) off-take agreements or LOIs with cell manufacturers before FID; (d) plant design allows capacity modulation (turndown to 25%) |
| OR6 | **Regulatory changes**: Changes to EU Battery Regulation, NZIA, or Innovation Fund rules during project implementation | Low | Low | **Low** | FIB (Legal / Regulatory) | (a) Project aligned with long-term EU strategic direction; (b) regulatory risk is downside-limited (any changes likely to increase, not decrease, demand for EU-manufactured low-carbon CAM); (c) monitoring of regulatory developments |
| OR7 | **Supply chain disruption**: Extended interruption of precursor supply (FePO4, Li2CO3) due to geopolitical events, logistics failures, or supplier insolvency | Low | High | **Medium** | FIB (Procurement Director) | (a) Dual-sourcing strategy; (b) minimum 3-month strategic inventory; (c) long-term supply agreements; (d) supplier financial health monitoring; (e) emergency spot market access |
| OR8 | **Quality certification delay**: Customer qualification of FACE LFP CAM takes longer than expected, delaying commercial revenue | Medium | Medium | **Medium** | FIB (Quality / Commercial) | (a) Early customer engagement with sample material from vendor trial batches (M24-M36); (b) qualification programme aligned with customer timelines; (c) DT-enabled consistency accelerates qualification (fewer qualification batches needed); (d) multiple customer qualification tracks in parallel |

### 9.3 Risk Heat Map

*Note: The visual risk heat map is to be created in the Word document. The following describes the positioning of each risk on a 5x5 probability/impact matrix.*

**5x5 Probability/Impact Matrix Description**:

- **Vertical axis**: Probability (1 = Very Low, 2 = Low, 3 = Medium, 4 = High, 5 = Very High)
- **Horizontal axis**: Impact (1 = Negligible, 2 = Low, 3 = Medium, 4 = High, 5 = Critical)
- **Risk zones**: Green (1-4), Yellow (5-9), Orange (10-15), Red (16-25)

| Risk ID | Probability Score | Impact Score | Risk Score | Zone |
|---------|------------------|-------------|------------|------|
| TR1 | 3 | 4 | 12 | Orange |
| TR2 | 3 | 3 | 9 | Yellow |
| TR3 | 3 | 3 | 9 | Yellow |
| TR4 | 2 | 3 | 6 | Yellow |
| TR5 | 3 | 4 | 12 | Orange |
| TR6 | 2 | 3 | 6 | Yellow |
| TR7 | 2 | 3 | 6 | Yellow |
| TR8 | 2 | 4 | 8 | Yellow |
| TR9 | 2 | 4 | 8 | Yellow |
| TR10 | 3 | 2 | 6 | Yellow |
| OR1 | 3 | 3 | 9 | Yellow |
| OR2 | 3 | 3 | 9 | Yellow |
| OR3 | 3 | 3 | 9 | Yellow |
| OR4 | 3 | 3 | 9 | Yellow |
| OR5 | 2 | 3 | 6 | Yellow |
| OR6 | 2 | 2 | 4 | Green |
| OR7 | 2 | 4 | 8 | Yellow |
| OR8 | 3 | 3 | 9 | Yellow |

**Summary**: Two risks in the Orange zone (TR1 calcination scale-up, TR5 product quality consistency) require priority attention through the piloting-before-procurement strategy and DT-driven quality control. All remaining risks are in the Yellow or Green zones, indicating manageable risk levels with the defined mitigation measures. No risks are assessed as Red (unacceptable).

The digital twin itself functions as a cross-cutting risk mitigation instrument: by providing real-time process visibility, predictive quality monitoring, and closed-loop control, the DT reduces the probability and impact of technical risks TR1-TR5 and TR7-TR10 during the operational phase [CLM-007].

---

## History of Changes

| Version | Date | Change |
|---------|------|--------|
| 1.0 | April 2026 | Initial draft for Innovation Fund submission |

---

*End of Feasibility Study*
