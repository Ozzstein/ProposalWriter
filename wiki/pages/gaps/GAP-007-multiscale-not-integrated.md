---
title: Multi-scale LFP models exist separately but are never integrated as a digital twin
type: gap
gap_id: GAP-007
created: 2026-04-16
updated: 2026-04-16
severity: high
strategic_importance: 8
gap_type: integration
addressed_by_projects: [faam-eni-circular-energy]
tags: []
---

# Multi-Scale LFP Models Exist Separately But Are Never Integrated as a Digital Twin

**Severity**: high | **Strategic importance**: 8/10 | **Type**: integration

## Description
A complete set of physics-based models for individual length scales of LFP synthesis exists in the literature: DFT/atomistic models for Li-Fe-P-O thermodynamics, CALPHAD phase diagrams, Jander/Avrami reaction kinetics, population balance models for particle size evolution, DEM for milling, and rotary kiln CFD. These models have been validated independently for their respective scales. However, they have never been integrated into a unified multi-scale digital twin framework that couples across scales and runs in real-time for production process control.

## Evidence
- [[sources/SRC-014]] — Multi-scale modeling literature covering CALPHAD, CFD, population balance, and kinetics models as separate publications
- [[sources/SRC-DT-REPORT]] — DT landscape report explicitly noting the integration gap: models exist at each scale but no unified DT has been assembled

## Addressed by
- **faam-eni-circular-energy**: A core technical work package develops the multi-scale integration architecture — connecting atomistic/CALPHAD thermodynamics to reactor-scale CFD to plant-level population balance — with surrogate model acceleration (neural network emulators) enabling real-time DT inference during production. This constitutes the project's primary scientific contribution.
