---
title: ISO 23247 Digital Twin Framework for Manufacturing
type: concept
created: 2026-04-16
updated: 2026-04-16
source_count: 4
tags: []
---

# ISO 23247 Digital Twin Framework for Manufacturing

## Overview
ISO 23247 is a four-part international standard (published 2021) that defines a reference architecture for manufacturing digital twins. The standard specifies four layers: (1) Observable Manufacturing Element (OME) — the physical asset and its measurable properties; (2) Device Communication — OPC-UA/MQTT-based real-time data exchange; (3) Domain Services — data processing, model execution, and analytics; (4) User — interfaces for operators, engineers, and systems. ISO 23247 is the de facto framework for interoperable, vendor-neutral manufacturing DT implementations in the EU and has multiple validated implementations in discrete manufacturing (machining, assembly, electronics). No published implementation exists for continuous thermal/chemical powder synthesis processes.

## Key findings
- ISO 23247 provides the validated four-layer DT framework with standardized OPC-UA data exchange (source: [[sources/SRC-007]])
- All documented implementations are in discrete manufacturing — no implementation exists for thermal/chemical synthesis (source: [[sources/SRC-008]])
- The standard's asset model requires non-trivial extension for reaction kinetics entities, gas-solid equilibrium services, and distributed temperature fields in continuous kilns (source: [[sources/SRC-009]])
- The faam-eni-circular-energy project will produce the first ISO 23247-compliant DT for thermal/chemical synthesis, with results proposed as input to ISO 23247-4 (conformance testing amendment) (source: [[sources/SRC-010]])

## Open questions
- How should ISO 23247 OME entities be defined for continuous rotary kiln processes where the "observable element" is a distributed material flow rather than a discrete workpiece?
- Is OPC-UA sufficient for the real-time sensor data rates required by in-line Raman (spectral acquisition at 1 Hz) and thermocouple arrays?
- What conformance testing regime is appropriate for a DT that integrates multi-scale physics models with real-time sensor data?

## Related concepts
- [[concepts/digital-twin-manufacturing]]
- [[concepts/process-analytical-technology]]
- [[concepts/calcination-cam-manufacturing]]
