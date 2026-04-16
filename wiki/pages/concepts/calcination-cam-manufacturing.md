---
title: Calcination and Sintering for Cathode Material Manufacturing
type: concept
created: 2026-04-16
updated: 2026-04-16
status: supported
source_count: 6
tags: []
---

# Calcination and Sintering for Cathode Material Manufacturing

## Overview
Calcination is the highest-temperature step in LFP CAM synthesis, transforming spray-dried precursor granules into the final crystalline olivine-structure LiFePO4 with carbon coating. In a continuous rotary kiln or roller hearth kiln operating at 600-800C under inert (N2/Ar) or slightly reducing atmosphere, precursor granules undergo sequential reactions: decomposition of carbonates and phosphates, intermediate phase formation, olivine LFP crystallization (Ea ~150-180 kJ/mol), and in-situ carbon coating from pyrolysis of the organic carbon source. Temperature profile, dwell time, atmosphere pO2, and heating/cooling rates are the primary control parameters determining phase purity, crystal size, carbon content, and electrochemical performance.

## Key findings
- LFP solid-state synthesis kinetics span 65-180 kJ/mol across sequential steps; precise temperature profile control is the primary quality determinant (source: [[sources/SRC-011]])
- Electric kilns achieve 95% thermal efficiency vs 25-60% for gas kilns, with direct implications for the energy cost and GHG footprint of LFP CAM calcination (source: [[sources/SRC-ED-009]])
- In-line Raman spectroscopy can simultaneously monitor olivine phase formation (950 cm-1), carbon coating quality (D/G ratio), and impurity phases during calcination — most information-rich single sensor for DT integration (source: [[sources/SRC-DT-REPORT]])
- Rotary kiln CFD models exist for continuous LFP calcination but have not been coupled to reaction kinetics or integrated into a real-time DT (source: [[sources/SRC-014]])
- TwinHeat (MINES Paris) provides the closest precedent: DT for industrial heat treatment furnaces using CFD + neural network surrogate + DRL (source: [[sources/SRC-DT-REPORT]])

## Open questions
- How does continuous kiln atmosphere (pO2 profile along kiln length) affect the Fe2+/Fe3+ ratio in final LFP and how is this monitored in-line?
- What is the minimum thermocouple array density needed for DT temperature field reconstruction in a 30m rotary kiln?
- Can electric roller hearth kiln control achieve tighter temperature uniformity than gas-fired RHK — and does this improve LFP phase purity?

## Related concepts
- [[concepts/lfp-cathode-active-material]]
- [[concepts/digital-twin-manufacturing]]
- [[concepts/electrification-process-heat]]
- [[concepts/iso-23247-digital-twin-framework]]
