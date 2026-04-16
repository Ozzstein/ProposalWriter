---
title: ISO 23247 has no implementation for thermal/chemical synthesis processes
type: gap
gap_id: GAP-005
created: 2026-04-16
updated: 2026-04-16
severity: high
strategic_importance: 8
gap_type: technology
addressed_by_projects: [faam-eni-circular-energy]
tags: []
---

# ISO 23247 Has No Implementation for Thermal/Chemical Synthesis Processes

**Severity**: high | **Strategic importance**: 8/10 | **Type**: technology

## Description
ISO 23247 (2021) provides a validated four-layer framework (observable manufacturing element, device communication, domain services, user) for manufacturing digital twins with multiple successful implementations in discrete manufacturing (machining, assembly, electronics). However, no published implementation exists for continuous thermal/chemical powder synthesis processes such as calcination, spray drying, or sintering. The standard's asset model and data exchange schema require non-trivial extension to handle time-varying reaction kinetics, gas-solid equilibria, and distributed temperature fields in continuous kilns and spray towers.

## Evidence
- [[sources/SRC-007]] — ISO 23247 standard text and framework description
- [[sources/SRC-008]] — ISO 23247 implementation survey: all cases in machining/assembly
- [[sources/SRC-009]] — ISO 23247 case studies confirming discrete manufacturing scope
- [[sources/SRC-010]] — DT standards review confirming thermal/chemical process application gap

## Addressed by
- **faam-eni-circular-energy**: The project will develop and validate the first ISO 23247-compliant DT for thermal/chemical powder synthesis, extending the standard's asset model with reaction kinetics entities, gas-solid equilibrium services, and distributed sensor fusion. Results will be contributed back as a proposed amendment to ISO 23247-4 (conformance testing).
