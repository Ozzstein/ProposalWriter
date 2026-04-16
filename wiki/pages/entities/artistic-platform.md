---
title: ARTISTIC Platform
type: entity
entity_type: platform
created: 2026-04-16
updated: 2026-04-16
source_count: 3
tags: []
---

# ARTISTIC Platform

## Overview
ARTISTIC (Advanced anode and cathode for lithium-ion batteries) is a physics-based digital twin platform for battery electrode manufacturing developed by the Franco research group at the University of Picardie Jules Verne (Amiens, France). It integrates multiphysics simulation of electrode slurry coating, drying, calendering, and electrolyte infiltration with Bayesian optimization for process parameter tuning. ARTISTIC has been validated for LFP and NMC electrode chemistry and is the most cited academic battery manufacturing DT in the EU.

## From: [[sources/SRC-003-artistic-platform]]
Documents the ARTISTIC platform architecture: four-layer computational framework (molecular dynamics → mesoscale → continuum → process), Bayesian optimization module for experimental iteration reduction, and validation results for LFP electrode manufacturing. Explicitly covers electrode coating and drying — does not extend to upstream CAM powder synthesis.

## From: [[sources/SRC-004-artistic-bayesian]]
Franco group publication demonstrating Bayesian optimization within ARTISTIC for electrode formulation, showing 40-60% reduction in experimental iterations to reach target porosity and tortuosity targets.

## From: [[sources/SRC-DT-REPORT]]
DT landscape report positions ARTISTIC as the EU benchmark for battery electrode manufacturing DTs. Confirms scope limitation: electrode level only, not CAM synthesis. Identifies ARTISTIC's architecture as a model for upstream CAM DT development.
