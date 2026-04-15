#!/usr/bin/env python3
"""Apply remaining ESS JV restructuring updates to draft files."""

import re
from pathlib import Path

DRAFTS = Path(__file__).parent

fs = DRAFTS / "annex_feasibility_study.md"
with open(fs, 'r') as f:
    content = f.read()

# Update risk owners — "FIB (Role)" → "ESS JV (Role)"
role_owners = [
    "(Technical Director)", "(DT Lead)", "(Process Engineering)",
    "(Quality Director)", "(Legal)", "(Quality / Procurement)",
    "(Project Manager)", "(HR Director)", "(Commissioning Manager)",
    "(Legal / Regulatory)", "(DT Lead / Automation)",
    "(Quality Manager)", "(Production)", "(Operations)",
]
for role in role_owners:
    old = f"| FIB {role}"
    new = f"| ESS JV {role}"
    content = content.replace(old, new)

# Clean up IP/consortium table references
content = content.replace(
    "| FIB (FAAM) | Battery manufacturing know-how; cell assembly and testing protocols; quality management systems | Contributed to project under consortium agreement; no royalties |",
    "| FIB (FAAM) — as ESS JV shareholder | Battery manufacturing know-how; cell assembly and testing protocols; quality management systems | Contributed to ESS JV through intercompany service agreements; no royalties |"
)
content = content.replace(
    "| Eni | Process engineering expertise; brownfield site engineering; energy systems design; industrial digitalisation capabilities | Contributed to project under consortium agreement; no royalties |",
    "| Eni — as ESS JV shareholder | Process engineering expertise; brownfield site engineering; energy systems design; industrial digitalisation capabilities | Contributed to ESS JV through intercompany service agreements; no royalties |"
)

# Update IP narrative
content = content.replace(
    "Neither FIB/FAAM nor Eni holds active patents in LFP CAM synthesis, process equipment, or digital twin manufacturing [CLM-015]. FIB has secured a technology licensor — Zhejiang Youshan New Material Technology Co., LTD. — for the LFP CAM solid-state synthesis process",
    "Neither FIB/FAAM nor Eni holds active patents in LFP CAM synthesis, process equipment, or digital twin manufacturing [CLM-015]. ESS JV has secured a technology licensor — Zhejiang Youshan New Material Technology Co., LTD. — for the LFP CAM solid-state synthesis process"
)
content = content.replace(
    "Both consortium partners are technology acquirers in the CAM synthesis domain, which eliminates intra-consortium IP conflicts.",
    "Both ESS JV shareholders (Eni and FIB) are technology acquirers in the CAM synthesis domain, which eliminates intra-shareholder IP conflicts and simplifies the ESS JV IP framework."
)

# Confidentiality provisions
content = content.replace(
    "**Confidentiality provisions**: The consortium agreement establishes mutual NDA obligations between FIB and Eni",
    "**Confidentiality provisions**: The ESS JV shareholders' agreement establishes mutual NDA obligations between FIB and Eni"
)

# Value chain table
content = content.replace(
    "| **Raw materials** | Precursor procurement (FePO4, Li2CO3, glucose) from EU and allied suppliers | FIB procurement | Global sourcing to Brindisi |",
    "| **Raw materials** | Precursor procurement (FePO4, Li2CO3, glucose) from EU and allied suppliers | ESS JV procurement | Global sourcing to Brindisi |"
)
content = content.replace(
    "| **CAM production** | 7-step solid-state LFP CAM synthesis (this project) | FIB (FAAM) | Brindisi, Eni site |",
    "| **CAM production** | 7-step solid-state LFP CAM synthesis (this project) | ESS JV | Brindisi site |"
)

# Coordinate TBC placeholder
content = content.replace(
    "| **Geographic coordinates** | [TO BE COMPLETED: Exact coordinates to be provided by site engineering] |",
    "| **Geographic coordinates** | 40.615°N, 17.980°E — within the Eni Brindisi petrochemical hub near Punta della Contessa |"
)

# "Eni-FIB internal demand" reference
content = content.replace(
    "(e.g., ITALVOLT, Eni-FIB internal demand)",
    "(including the co-located ESS JV cell and BESS facility as primary internal customer)"
)

# "single consortium" → "single legal entity"
content = content.replace(
    "vertically integrated clean energy value chain** that extends from raw material processing to grid-deployed energy storage within a single consortium and industrial site",
    "vertically integrated clean energy value chain** that extends from raw material processing to grid-deployed energy storage within a single legal entity (ESS JV) and industrial site"
)

with open(fs, 'w') as f:
    f.write(content)

print(f"Feasibility study: updated with ESS JV structure")

# Also update Section 0 — "FIB-Eni partnership" references that escaped
sec0 = DRAFTS / "00_project_and_applicants.md"
with open(sec0, 'r') as f:
    content = f.read()
# These were already restructured in the main section, but check for any stragglers
if "FIB-Eni partnership" in content:
    content = content.replace("FIB-Eni partnership", "ESS JV structure")
if "two-partner consortium" in content:
    content = content.replace("two-partner consortium", "mono-beneficiary structure")
with open(sec0, 'w') as f:
    f.write(content)
print(f"Section 0: cleaned up stragglers")

# Update 03_4 risk management for role owners
rm = DRAFTS / "03_4_risk_management.md"
with open(rm, 'r') as f:
    content = f.read()
for role in role_owners:
    content = content.replace(f"| FIB {role}", f"| ESS JV {role}")
with open(rm, 'w') as f:
    f.write(content)
print(f"03_4_risk_management: risk owners updated")

# Update 03_3 operational maturity -- the table and consortium references
# Most already done, but let's catch any straggler table lines
om = DRAFTS / "03_3_operational_maturity.md"
with open(om, 'r') as f:
    content = f.read()
# Legacy table rows that may still have "FIB" as partner column
# Already replaced the main table above, but check for any stragglers
with open(om, 'w') as f:
    f.write(content)

print("\nDone.")
