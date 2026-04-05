# Project Context: FAAM-ENI Circular Energy

## Project Title
**FAAM-ENI Circular Energy: Digital Twin-Driven LFP Active Material Manufacturing**

## Research Topic
Development and implementation of a digital twin (DT) framework to enable LFP cathode active material (CAM) production in a new production plant — the first in Italy and southern Europe — at Eni's Brindisi brownfield site, as part of a vertically integrated clean energy value chain from cathode material to grid-deployed battery energy storage.

Key differentiators:
- **Electrified manufacturing**: LFP production using electrical energy (especially during spray drying and calcination), in contrast to the state-of-the-art Asian suppliers who rely predominantly on natural gas
- **Digital twin integration**: ISO 23247-compliant real-time process twin, predictive quality monitoring, and new-generation material discovery
- **Brownfield conversion**: Repurposing an existing Eni industrial site in Brindisi, Italy
- **Vertically integrated value chain**: LFP CAM (this project) feeds a co-located FIB-Eni JV battery cell and BESS factory at Brindisi; Eni deploys the BESS on the Italian electricity grid for grid stabilisation and decarbonisation. Eni is the guaranteed internal offtaker.
- **GHG classification**: ES / Manufacturing of Components (Section 1.3.2). GHG avoidance calculated on BESS use-phase displacing fossil peakers, not on manufacturing plant emissions.

## Funding Agency and Instrument
- **Call**: INNOVFUND-2025-NZT-CLEAN-TECH-MANUFACTURING
- **Agency**: European Climate, Infrastructure and Environment Executive Agency (CINEA)
- **Instrument**: Innovation Fund — Clean-tech manufacturing topic
- **Deadline**: 23 April 2026, 17:00 CET

## Key Hypothesis / Central Idea
Using electricity instead of gas in LFP CAM manufacturing, coupled with an integrated digital twin framework, will:
1. **Significantly reduce CO2 emissions** compared to conventional gas-fired LFP production (predominantly Asian benchmark)
2. **Improve GHG performance** through electrification of energy-intensive steps (spray drying, calcination)
3. **Enable real-time process optimization** via an ISO 23247 Layer 4 process twin
4. **Deliver predictive quality monitoring** reducing batch-to-batch variability and scrap rates
5. **Accelerate material discovery** through multi-scale simulation (DFT to plant scale)

## Team Members and Roles
| Partner | Role | Description |
|---------|------|-------------|
| **FIB (FAAM)** | Main applicant / Coordinator | Battery manufacturer, responsible for LFP CAM plant construction and operation |
| **Eni** | Co-investigator and guaranteed offtaker | Energy company, brownfield site owner (Brindisi), expertise in process engineering and energy supply. Partner in co-located JV battery cell and BESS factory. Will deploy BESS on Italian electricity grid. |
| **FIB-Eni JV** | Co-located battery factory | Joint venture battery cell and BESS manufacturing facility at Brindisi site; direct internal customer for LFP CAM output |

## Preliminary Data and Prior Work

### 1. Digital Twin Framework Deep-Dive Report (35 pages)
Comprehensive technical analysis covering:
- **LFP synthesis routes**: Solid-state, hydrothermal, co-precipitation, sol-gel, spray pyrolysis — with solid-state as the dominant industrial route
- **Multi-scale modeling framework**: DFT/atomistic → MD → mesoscale (phase-field, KMC) → continuum (CFD, PBM, FEM) → plant (flowsheet simulation)
- **Physics-based process models**: CALPHAD thermodynamics, rotary kiln CFD, population balance models, DEM for milling, multi-step reaction kinetics (Jander, Avrami, shrinking core)
- **Sensor technologies & PAT**: Temperature (thermocouples, pyrometers, IR cameras), particle size (FBRM, laser diffraction), chemical composition (Raman, XRF, XRD), atmosphere monitoring (O2, CO2, mass spec)
- **ISO 23247 four-layer architecture**: Observable Manufacturing Element → Data Collection & Device Control → Digital Twin Core → User Entity
- **Data architecture**: Edge-fog-cloud with OPC-UA, MQTT, InfluxDB, HDF5, Delta Lake
- **QbD framework**: CQA/CPP mapping — key CQAs include D50 (1-3 μm), BET (12-18 m²/g), phase purity (>98% olivine), carbon content (1.5-3.0 wt%), discharge capacity (>155 mAh/g)
- **Case studies**: ARTISTIC platform (Franco et al.), TwinHeat (MINES Paris), Fraunhofer ITWM DiBaZ
- **Key finding**: DT can reduce scrap rates by 10-50%, energy consumption by 12-15%, and batch-to-batch variability by >40%

### 2. LFP CAM Process Flow (in Italian)
7-step manufacturing process:
1. Raw materials dosing (iron phosphate, lithium carbonate, glucose) into dispersion tank
2. Sand milling → particle size verification → magnetic particle removal (demagnetizer)
3. Spray drying — aqueous mixture dried to solid unreacted mixture
4. Crucible loading → furnace calcination at process temperature (via external rail)
5. Jet milling (air-flow grinding)
6. Ultrasonic vibrating sieve → electromagnetic dry powder separator (demagnetization)
7. Automated packaging of finished LiFePO4 product

## Call Alignment Notes

### Topic Scope Match (CLEAN-TECH-MANUFACTURING)
- **Energy storage**: Production of batteries and other storage solutions — LFP CAM is a battery cathode material ✓
- **Innovation in production processes**: Lower environmental/carbon footprint, improved automation and use of digital technologies ✓
- **Innovation in products**: Higher performance, more energy efficiency ✓

### Scoring (Weighted for CLEAN-TECH-MANUFACTURING)
| Criterion | Max Score | Weight | Weighted Max | Min Pass |
|-----------|-----------|--------|--------------|----------|
| Degree of Innovation | 15 | ×2 | **30** | 9 |
| GHG Emission Avoidance | 12 | ×1 | **12** | varies |
| Project Maturity | 15 | ×2 | **30** | 3/sub |
| Replicability | 15 | ×1 | **15** | 4 (EU leadership) |
| Cost Efficiency | 15 | ×1 | **15** | 1.5 (quality) |
| **Total (weighted)** | | | **102** | |
| Bonus points | 3 | ×1 | **3** | |
| **Grand Total** | | | **105** | |

### Key Requirements
- Relative GHG emission avoidance ≥ 50%
- Cost efficiency ratio ≤ 200 EUR/tCO2-eq
- Part B page limit: 70 pages (Arial 9pt, A4, 15mm margins)
- Financial close within 48 months of grant agreement (bonus for within 2 years)
- Entry into operation bonus for within 4 years

### Strategic Positioning
- **First LFP CAM plant in Italy/Southern Europe** — strong EU strategic autonomy argument
- **Vertically integrated value chain** — LFP CAM to cells to BESS to Italian grid, mine-to-grid within one consortium/site
- **Eni as guaranteed internal offtaker** — eliminates offtake risk; BESS deployed on Italian grid
- **GHG classification: ES / Manufacturing of Components** — avoidance calculated on BESS use-phase displacing fossil peakers
- **Reducing dependency on Chinese LFP supply** — directly addresses NZIA/STEP objectives
- **Brownfield site reuse** — circular economy alignment
- **Electrification of process heat** — innovation and replicability argument (NOT the GHG argument)
- **Digital twin** — innovation beyond state-of-the-art in manufacturing process control
