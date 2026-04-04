# Section 4 — Replicability

## 4.1a Replicability in Terms of Efficiency Gains and Multiple Environmental Impacts

### Efficient Use of Critical Raw Materials

The FAAM-ENI Circular Energy project is strategically positioned around **LFP chemistry (LiFePO4)**, which offers fundamental advantages in critical raw material efficiency compared to nickel-cobalt-manganese (NMC) and nickel-cobalt-aluminium (NCA) cathode chemistries that dominate the current European battery supply chain:

**Iron and phosphorus abundance.** LFP uses iron — the fourth most abundant element in the Earth's crust — as its transition metal, eliminating dependency on cobalt (a conflict mineral with concentrated supply in the DRC) and nickel (subject to significant price volatility and geopolitical supply risk). Phosphorus, sourced as iron phosphate (FePO4), is the binding constraint among LFP feedstocks, but global phosphate rock reserves exceed 70 billion tonnes with diversified geographic supply Iron phosphate consumption is 0.98 t per tonne of LFP CAM (49,000 t/yr at full capacity). Global phosphate rock reserves exceed 70 billion tonnes with diversified geographic supply (USGS Mineral Commodity Summaries).

**Lithium efficiency.** LFP requires approximately 42 g Li per kWh of cell capacity compared to 50-75 g/kWh for NMC chemistries, representing a 20-44% reduction in lithium intensity per unit of stored energy lithium intensity comparison based on stoichiometric calculations; the Brindisi plant consumes 0.25 t Li2CO3 per tonne LFP CAM (12,500 t/yr at full 50 kton/yr capacity).

**Digital twin-driven material yield optimisation.** The integrated DT framework directly reduces raw material waste through two mechanisms: (1) predictive quality control reduces scrap rates by 10-50% [CLM-007], meaning fewer rejected batches consuming lithium, iron phosphate, and glucose inputs; and (2) real-time process parameter optimisation via model-predictive control minimises off-specification product that would require reprocessing or disposal. The Fraunhofer FFB demonstrated a 10.3% scrap rate reduction using DT-guided process optimisation in battery cell production [CLM-017] — the FAAM DT extends this approach upstream to CAM synthesis where material losses are proportionally more costly.

### Circular Economy and Recyclability

LFP chemistry provides intrinsic circular economy advantages:

**Simplified recycling pathway.** The absence of cobalt and nickel in LFP eliminates the most complex and environmentally hazardous steps in cathode recycling (selective precipitation of Co/Ni from mixed metal solutions). LFP recycling focuses on lithium recovery — a less technically challenging separation — and iron phosphate recovery for direct re-use as precursor material. This positions the Brindisi plant's output as inherently more recyclable than NMC/NCA alternatives within the emerging EU Battery Regulation recycling framework.

**Brownfield site reuse.** The project converts an existing Eni industrial site in Brindisi (Puglia) from fossil fuel-related operations to clean-tech manufacturing, directly embodying circular land use principles. No greenfield land is consumed. Existing industrial infrastructure — utility connections, road/rail/port access, wastewater treatment capacity, electrical grid connections — is repurposed, avoiding the embodied carbon and environmental impact of new infrastructure development [CLM-022].

**DT-enabled waste minimisation.** The digital twin's Quality-by-Design framework systematically maps Critical Quality Attributes (D50 particle size 0.7-2.5 micrometer, SSA 10-14 m2/g, olivine phase purity >98%, carbon content 1.0-1.8 wt%) to Critical Process Parameters [CLM-009], enabling right-first-time production that minimises process waste streams. Batch-to-batch variability reduction (>40% demonstrated in comparable DT implementations [CLM-007]) directly reduces the volume of off-specification material requiring rework or disposal.

### Water Management

LFP CAM production via the solid-state spray drying route uses water as a dispersing medium in the slurry preparation stage. The spray drying step evaporates this water to produce dry precursor powder. The Brindisi facility implements a **closed-loop water recovery system** for the spray dryer: exhaust air from the spray dryer passes through condensation and filtration stages to recover evaporated water for recirculation to the slurry mixing tanks. This closed-loop design reduces freshwater intake by an estimated 70-85% compared to once-through water use water recovery efficiency estimate based on industrial spray dryer condensate recovery systems. The production document specifies 4 t production water and 5 t pure water per tonne LFP CAM; exact recovery rate to be optimised during detailed engineering.

No process water is discharged to surface water or marine environments. All non-recoverable water exits the facility as vapour in exhaust air (after HEPA filtration to remove particulate matter).

### Pollution Prevention

The electrified production design eliminates several pollution sources inherent to gas-fired LFP CAM manufacturing:

- **Drastically reduced on-site combustion emissions**: The progressive electrification strategy minimises natural gas use (189 m3/t in initial configuration versus fully gas-fired benchmark), dramatically reducing NOx, SOx, CO, and particulate matter emissions. Conventional gas-fired rotary kilns generate approximately 0.5-2.0 kg NOx per tonne of product; the Brindisi plant's limited residual gas use produces a fraction of these emissions, with the pathway to full electrification eliminating them entirely [CLM-011].
- **Contained atmosphere processing**: Calcination under inert N2 atmosphere (pO2 <10 ppm) prevents formation of Fe2O3 dust and eliminates fugitive iron oxide emissions [CLM-009].
- **HEPA filtration**: All air handling systems incorporate HEPA filters to capture fine LFP powder (D50 1-3 micrometer range), preventing release of nano-scale particles to the environment.
- **Closed milling systems**: Jet milling and ultrasonic sieving operate in enclosed systems with integrated dust collection, preventing fugitive dust emissions.

### Biodiversity Protection

The Brindisi site is a **designated industrial brownfield** within an existing industrial zone. No greenfield conversion is involved. The project does not encroach on protected habitats, Natura 2000 sites, or areas of high biodiversity value. By repurposing an existing industrial site, the project avoids habitat conversion, soil sealing, and ecosystem fragmentation that would accompany a greenfield development. Where remediation of legacy contamination from prior fossil fuel operations is required, this represents a net positive for local environmental quality.

---

## 4.1b Compliance with DNSH Technical Screening Criteria for Environmental Objectives Other Than Climate Change Mitigation

The DNSH compliance assessment for the five remaining environmental objectives under Regulation (EU) 2020/852 is presented below. Climate change mitigation was addressed in Section 2.3.

### 1. Climate Change Adaptation

**Assessment:** The Brindisi facility is located in a coastal Mediterranean industrial zone in Puglia, Southern Italy. The site is exposed to climate change-related risks including increased summer temperatures (projected +1.5-2.5 C by 2050 under RCP4.5), intensified precipitation events, and potential coastal flooding/storm surge amplification.

**Mitigation measures:**
- **Heat resilience**: Electric process equipment (roller hearth kilns, spray dryers) operates at design temperatures of 600-800 C and is inherently insensitive to ambient temperature fluctuations of 2-3 C. Building HVAC and DT server room cooling systems are designed with a 3 C safety margin above projected 2050 peak temperatures. Industrial operations are less vulnerable to heat stress than office environments; worker protection follows Italian D.Lgs. 81/2008 occupational heat stress protocols.
- **Flood and storm surge resilience**: Site engineering incorporates a minimum 0.5 m elevation above the 500-year flood level (including sea level rise projections to 2070). Critical electrical infrastructure (transformers, DT server rooms, control systems) is elevated or flood-protected. Drainage systems are designed for a 1-in-100-year precipitation event with a 20% climate change allowance.
- **Supply chain resilience**: Raw material storage provides a minimum 30-day buffer stock to mitigate disruption from extreme weather events affecting transport infrastructure. The DT's predictive scheduling module adjusts production planning to accommodate weather-related disruptions.

**Compliance confirmation:** The project has conducted a proportionate climate risk and vulnerability assessment consistent with Annex A of the Taxonomy Climate Delegated Regulation. Adaptation measures are integrated into the facility design. The project does not increase the vulnerability of surrounding human or natural systems to climate change.

### 2. Protection of Water and Marine Resources

**Assessment:** Brindisi is a coastal city on the Adriatic Sea. The industrial zone has existing wastewater treatment infrastructure. LFP CAM production has a relatively low water footprint compared to NMC co-precipitation (which generates significant wastewater streams from washing and pH adjustment steps).

**Mitigation measures:**
- **Closed-loop water system**: Spray dryer condensate recovery recirculates process water, reducing freshwater demand by 70-85%. The production document specifies 4 t production water and 5 t pure water per tonne LFP CAM; exact recovery rate to be optimised during detailed engineering.
- **Zero industrial discharge**: No process wastewater is discharged to surface water, groundwater, or marine environments. Non-recoverable water exits as vapour after HEPA filtration.
- **Stormwater management**: Site drainage separates clean stormwater from potentially contaminated runoff (e.g., from loading areas). Contaminated runoff is directed to the industrial wastewater treatment system.
- **Chemical containment**: All liquid chemical storage (lithium carbonate slurry, iron phosphate suspension) is within bunded areas with 110% containment capacity to prevent release to ground or water.

**Compliance confirmation:** The project does not degrade the status of water bodies or the potential for water bodies to achieve good ecological status. The facility design prevents industrial discharge to water resources.

### 3. Transition to a Circular Economy

**Assessment:** The project contributes to circular economy objectives through multiple pathways.

**Design for circularity:**
- **LFP recyclability**: The project's output (LFP CAM) is inherently more recyclable than NMC/NCA alternatives due to the absence of cobalt and nickel, which simplify hydrometallurgical recovery processes. LFP recycling enables direct lithium recovery and iron phosphate re-use as precursor.
- **Waste minimisation**: DT-driven quality control reduces scrap and off-specification production. The QbD framework establishes process design spaces that maximise first-pass yield [CLM-009, CLM-013].
- **Process waste streams**: Calcination off-gases (primarily N2 + CO2 from glucose pyrolysis) are filtered and vented; no hazardous waste streams are generated. Milling fines below specification are recycled into the slurry preparation stage. Packaging waste (raw material containers) follows standard industrial recycling channels.
- **Equipment durability**: Electric roller hearth kilns have longer operational lifetimes than gas-fired equivalents (fewer thermal cycling stresses, no combustion-related corrosion), reducing equipment replacement frequency and associated waste.

**Compliance confirmation:** The project does not lead to significant inefficiencies in the use of materials or in the direct or indirect use of natural resources. The production process is designed to maximise material yield, minimise waste, and produce an inherently recyclable output product.

### 4. Pollution Prevention and Control

**Assessment:** LFP CAM production involves handling of fine powders (lithium carbonate, iron phosphate, LFP product) and elevated-temperature processing under controlled atmosphere.

**Mitigation measures:**
- **Air emissions**: Minimal on-site combustion (progressively electrified design with residual gas use of 189 m3/t in initial configuration, decreasing over time). HEPA filtration on all powder handling exhausts. Calcination atmosphere is contained (sealed kiln with N2 blanket). No volatile organic compound (VOC) emissions — glucose carbon precursor is pyrolysed under inert atmosphere, not volatilised.
- **Chemical safety**: All chemicals used (lithium carbonate, iron phosphate, glucose) are classified as low to moderate hazard under CLP Regulation (EC) No 1272/2008. No SVHC (Substances of Very High Concern) or REACH Annex XIV substances are used in the production process. Lithium carbonate requires standard occupational hygiene measures (dust control, PPE) but is not classified as acutely toxic.
- **Noise**: Electric motors and kilns generate significantly lower noise levels than gas combustion equipment (no combustion roar, no gas valve cycling). Site noise levels at the boundary are expected to comply with Italian DPCM 14/11/1997 industrial zone limits.
- **Waste management**: No hazardous waste streams are generated. Solid waste (packaging, maintenance consumables, HEPA filters) is managed through licensed industrial waste contractors in accordance with Italian D.Lgs. 152/2006.

**Compliance confirmation:** The project does not lead to a significant increase in emissions of pollutants to air, water, or land. The fully electrified design and contained atmosphere processing eliminate the principal pollution sources associated with conventional gas-fired CAM production.

### 5. Protection and Restoration of Biodiversity and Ecosystems

**Assessment:** The project is located entirely within an existing industrial zone at Eni's Brindisi brownfield site. No greenfield land conversion is involved.

**Mitigation measures:**
- **No habitat conversion**: The site is an existing industrial facility. No natural or semi-natural habitats, agricultural land, or forested areas are affected. No Natura 2000 sites are impacted.
- **Brownfield remediation**: Where legacy contamination from prior industrial operations exists, the project's site preparation includes remediation to applicable Italian standards (D.Lgs. 152/2006 Parte IV, Titolo V), representing a net improvement in local environmental quality.
- **Light and noise**: Industrial operations are contained within enclosed buildings, minimising light pollution and noise impacts on surrounding ecosystems. Operating hours and lighting follow standard industrial zone protocols.

**Compliance confirmation:** The project does not significantly harm biodiversity or ecosystems. The brownfield location ensures zero habitat conversion, and remediation activities provide a net environmental benefit.

---

## 4.1c Contribution to Europe's Industrial Leadership and Competitiveness

### EU Industrial Ecosystems: Anchoring the European Battery Value Chain

The FAAM-ENI Circular Energy project establishes the **first LFP cathode active material production facility in Italy and Southern Europe** [CLM-022], directly filling a critical gap in the European battery value chain. As of late 2025, no EU-based company has brought LFP CAM production online [CLM-003], despite LFP being the fastest-growing cathode chemistry globally and the dominant choice for standard-range EVs and grid-scale storage applications.

The Brindisi plant is positioned to supply European battery cell manufacturers — including the growing gigafactory ecosystem across Germany, France, Hungary, Poland, and Scandinavia — with domestically produced, EU-traceable LFP cathode material. This creates a new node in the EU battery supply chain that currently does not exist, connecting:

- **Upstream**: European and allied-nation suppliers of lithium carbonate, iron phosphate, and industrial-grade glucose
- **Midstream**: FAAM Brindisi LFP CAM production (this project)
- **Downstream**: European battery cell manufacturers (e.g., ACC, Northvolt, PowerCo, Samsung SDI Hungary, SK On Hungary, CATL Germany/Hungary) requiring LFP cathode material for next-generation LFP cells

The plant's location in Puglia — a Cohesion Policy convergence region — provides geographic diversification within the emerging EU LFP supply map, complementing FREYR's Northern European site (Vaasa, Finland) and ensuring Mediterranean access for Southern European cell manufacturers and export markets.

### Reducing EU Dependency on China: Directly Addressing C/2025/3236

**This project directly mitigates one of the most acute supply chain dependencies identified by the European Commission.** China controls over 99% of global LFP cathode active material production capacity [CLM-001]. Commission Communication C/2025/3236 of 18 June 2025 explicitly identified battery cells, battery packs, and battery materials as products with critical EU dependency on China, requiring urgent mitigation under the Net-Zero Industry Act.

The urgency of this dependency has escalated sharply:

- **July 2025**: China imposed export licensing requirements on 4th-generation LFP cathode technology, directly restricting technology transfer [CLM-002].
- **October 2025**: China broadened export controls to include battery cells, precursors, anode materials, and production equipment [CLM-002].
- **Strategic implication**: The EU battery industry faces a dual risk — dependency on Chinese LFP CAM imports for current production AND dependency on Chinese technology and equipment for any future EU-based LFP CAM manufacturing.

The FAAM Brindisi plant addresses both dimensions of this dependency:

1. **Product supply**: Domestic LFP CAM production reduces import dependency for the material itself.
2. **Technology sovereignty**: The project develops an EU-originated DT-integrated manufacturing process, generating proprietary know-how within the EU/EEA that is not subject to Chinese export control restrictions.

**Competitive landscape assessment.** FREYR Battery received a EUR 122M Innovation Fund grant for a 30,000 t/yr LFP CAM facility in Vaasa, Finland [CLM-004]. However, FREYR's current corporate strategy prioritises its US Giga America facility. FREYR has stated it is "evaluating options" for its Norwegian and European asset base, and the Vaasa CAM facility has not reached Final Investment Decision (FID). Vaasa competes internally with FREYR's US operations for capital and management bandwidth [CLM-029]. Realistic assessment: FREYR Vaasa is a medium-term option with non-trivial schedule and financing risk — not a near-term locked-in LFP CAM production line. The FAAM Brindisi project, backed by FIB's manufacturing expertise and Eni's industrial site and energy infrastructure, represents the more credible near-term pathway to operational EU LFP CAM capacity.

### Building European Know-How: DT Framework as Transferable EU IP

The project generates intellectual property and technical know-how that remains within the EU/EEA:

**ISO 23247 reference implementation for chemical manufacturing.** The digital twin framework — the first ISO 23247-compliant implementation for thermal/chemical powder synthesis [CLM-008] — constitutes a replicable reference architecture transferable to other EU manufacturers of cathode materials, battery-grade precursors, and advanced ceramic powders. The four-layer architecture (Observable Manufacturing Element, Data Collection & Device Control, Digital Twin Core, User Entity) with its physics-based process models, sensor fusion algorithms, and model-predictive control strategies represents substantial technical IP developed entirely within the EU/EEA.

**Multi-scale modeling framework.** The integrated modeling chain spanning DFT/atomistic thermodynamics (CALPHAD) through continuum CFD and population balance models to plant-level flowsheet simulation [CLM-018] provides a transferable computational methodology for process optimisation in adjacent EU manufacturing sectors (e.g., catalysts, pigments, functional ceramics, pharmaceutical granulation).

**Patent strategy.** The core novel combination — electrified spray drying + electric roller hearth kiln calcination with integrated ISO 23247 digital twin for real-time process-quality control for LFP CAM — occupies a patent white space with no identified blocking patent [CLM-014]. The consortium intends to file EU patent applications protecting the DT-integrated electrified CAM manufacturing process, ensuring this IP remains within the EU/EEA.

### Cooperation with EU Research Institutions

The project engages EU/EEA universities and research institutions in the development and validation of the DT framework:

- **Italian universities**: Collaboration with leading Italian academic institutions for multi-scale modeling development and DT validation. Candidate university partners based on relevant expertise include:
  - **Politecnico di Milano**: A leading European university in digital twin research, hosting the DigiTwin conference and home to the I4.0 Lab and SuPER team (digital twin for chemical engineering). Elisa Negri (recipient of the Digital Twin Young Scientist Award) leads relevant research on manufacturing digital twins.
  - **Politecnico di Torino**: Home to the GAME Lab (Group for Applied Materials and Electrochemistry), with deep expertise in LFP and cathode materials, battery electrochemistry, and nanostructured materials. The GAME Lab maintains active PhD programmes with industrial partners (including Comau and Stellantis), providing a natural framework for collaborative research.
  - FIB/FAAM has an established track record of supporting research with universities through PhD studentships and MSc degree collaborations, providing the institutional framework for these partnerships. Specific collaboration agreements to be formalised during WP1.
- **EU research networks**: Engagement with the EU Battery Alliance ecosystem and relevant Horizon Europe projects for DT methodology cross-fertilisation.
- **Standards contribution**: The ISO 23247 reference implementation for chemical manufacturing will be documented and contributed to ISO TC 184 (Automation systems and integration) working groups, strengthening EU influence on international manufacturing digitalisation standards.

### Capacity Building and Job Creation

The Brindisi facility creates direct employment in Puglia, an EU Cohesion Policy convergence region with high structural unemployment. The project delivers:

- **Direct manufacturing employment**: Operators, process engineers, quality control technicians, and maintenance staff for the 4-line, 50 kton/yr LFP CAM production facility [TO BE COMPLETED: specific FTE numbers to be provided by FIB HR planning].
- **Digital skills development**: A dedicated training programme for DT operators — skilled technicians who combine process engineering knowledge with data science and model-based control expertise. This cross-disciplinary skillset is essential for Industry 4.0 manufacturing and currently scarce in Southern Europe.
- **Supply chain employment**: Indirect job creation through local suppliers of utilities, logistics, maintenance services, and raw material handling.
- **Apprenticeship and internship programmes**: Structured programmes in partnership with Puglia-region vocational training institutions and universities, building a pipeline of skilled workers for the emerging EU battery manufacturing sector.

### Supply Chain Due Diligence

The project implements comprehensive supply chain governance aligned with EU expectations:

- **Transparency**: EU-based supply chain with full traceability from raw material procurement to finished LFP CAM product. The DT's data architecture (OPC-UA/MQTT, time-series databases, edge-fog-cloud) inherently captures the provenance and process data required for the EU Battery Passport (mandatory from 2027).
- **Governance standards**: All suppliers are subject to FIB/Eni procurement standards covering governance, anti-corruption, labour rights, and environmental performance.
- **Environmental performance**: Supplier environmental assessments cover water risk, emissions, waste management, and biodiversity impacts, aligned with the CSRD (Corporate Sustainability Reporting Directive) framework.
- **Conflict mineral avoidance**: LFP chemistry eliminates cobalt — the battery material most associated with conflict mineral sourcing concerns — removing the single most difficult due diligence challenge in battery supply chains.
- **Human and social rights**: Lithium sourcing follows EU Critical Raw Materials Act due diligence requirements. Iron phosphate and glucose are sourced from established industrial supply chains with no identified human rights red flags.

### EEA-Originating Content

The Brindisi facility is located in Italy (EU Member State). The LFP CAM product is manufactured entirely within the EU/EEA. Key equipment and technology components:

- **Manufacturing equipment**: Electric roller hearth kilns, spray dryers, jet mills, and ultrasonic sieving equipment sourced from EU/EEA and allied-nation suppliers where available (e.g., Kanthal/Sandvik for electric heating elements — Sweden; NGK or equivalent for roller hearth kiln systems).
- **DT infrastructure**: Software development, modeling frameworks, and data architecture developed within EU/EEA.
- **Process know-how**: The integrated DT-electrified manufacturing process is developed entirely within the EU/EEA consortium.

The declaration on equipment/components EEA-originating content (mandatory deliverable in the last year of operation for CLEAN-TECH-MANUFACTURING projects) will be prepared and submitted as part of the final work package.

---

## 4.2 Knowledge Sharing — Communication, Dissemination, and Visibility

The FAAM-ENI Circular Energy project commits to an ambitious knowledge sharing programme that extends beyond mandatory requirements, reflecting the project's strategic importance for EU battery sovereignty.

### Technical and Scientific Publications

- **Peer-reviewed publications**: A minimum of 3 peer-reviewed publications over the project lifetime, targeting journals such as Journal of Power Sources, Journal of The Electrochemical Society, and Computers & Chemical Engineering. Publication topics include: (1) the ISO 23247 reference implementation for chemical powder manufacturing; (2) multi-scale modeling methodology for LFP CAM synthesis; (3) electrified LFP CAM production energy and GHG performance data (the first published LFP-specific data, addressing the research gap identified in CLM-028).
- **Conference presentations**: Annual presentations at major EU battery and manufacturing conferences (EU Battery Alliance events, The Battery Show Europe, ACHEMA, Digital Twin Conference).

### Open-Source DT Framework Components

Where commercially non-sensitive, the project will release open-source components of the DT framework:
- ISO 23247 reference architecture documentation for chemical manufacturing (layer specifications, interface definitions, data schemas)
- Validated surrogate models for generic spray drying and calcination unit operations (without proprietary LFP-specific parameters)
- Data integration templates for OPC-UA/MQTT sensor-to-DT data pipelines

This approach balances IP protection for the consortium with the EU objective of building a shared knowledge base for manufacturing digitalisation.

### Site Visits and Stakeholder Engagement

- **Annual site visits**: The Brindisi facility will host annual site visits for EU battery ecosystem stakeholders, including cell manufacturers, equipment suppliers, policy makers, and research institutions. Visits include production line tours (within IP constraints), DT demonstration, and technical discussion sessions.
- **EU Battery Alliance engagement**: Active participation in EU Battery Alliance working groups on manufacturing digitalisation and cathode material production.

### Training Programmes

- **DT operator training curriculum**: Developed in partnership with regional vocational institutions, the training programme will be documented and made available as a replicable template for other EU manufacturers implementing digital twin systems.
- **Masterclass series**: Annual 2-day technical masterclasses on DT-driven manufacturing for industry participants, combining lectures with hands-on simulation exercises using the project's validated models.

### Annual Knowledge Sharing Reports

As a mandatory deliverable, knowledge sharing reports will be submitted at each milestone (financial close, entry into operation, annually during operational monitoring). These reports will document:
- Technical progress and lessons learned
- Publications and presentations completed
- Site visits conducted and stakeholder feedback
- Training programmes delivered and participants reached
- Open-source releases and adoption metrics

### EU Funding Visibility

All project communications, publications, technical documentation, and site signage will prominently display:
- The EU flag and Innovation Fund logo
- The acknowledgment text: "This project has received funding from the Innovation Fund of the European Union"
- The grant agreement number and project acronym

Visibility measures comply with the grant agreement communication and dissemination obligations and the Innovation Fund branding guidelines.
