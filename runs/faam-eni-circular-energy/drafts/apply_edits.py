#!/usr/bin/env python3
"""Apply all 10 factual corrections to proposal drafts."""

import re
import os
import json
from pathlib import Path

DRAFTS = Path(__file__).parent
MEMORY = DRAFTS.parent / "memory"

def replace_in_file(filepath, old, new, count_only=False):
    """Replace old with new in file. Returns count of replacements."""
    with open(filepath, 'r') as f:
        content = f.read()
    n = content.count(old)
    if n > 0 and not count_only:
        content = content.replace(old, new)
        with open(filepath, 'w') as f:
            f.write(content)
    return n

def regex_replace_in_file(filepath, pattern, replacement):
    """Regex replace in file. Returns count."""
    with open(filepath, 'r') as f:
        content = f.read()
    new_content, n = re.subn(pattern, replacement, content)
    if n > 0:
        with open(filepath, 'w') as f:
            f.write(new_content)
    return n

total_changes = 0

# Get all md and json files
md_files = list(DRAFTS.glob("*.md"))
json_files = list(DRAFTS.glob("*_meta.json"))
all_files = md_files + json_files

print("=" * 60)
print("CHANGE 1: Calcination temperature 600-700/650-700 → 700-800")
print("=" * 60)
for f in all_files:
    n1 = replace_in_file(f, "650-700 C", "700-800 C")
    n2 = replace_in_file(f, "600-700 C", "700-800 C")
    n3 = replace_in_file(f, "650–700", "700–800")
    n4 = replace_in_file(f, "600–700", "700–800")
    n = n1 + n2 + n3 + n4
    if n > 0:
        print(f"  {f.name}: {n} replacements")
        total_changes += n

print()
print("=" * 60)
print("CHANGE 5: In-line Raman → At-line Raman")
print("=" * 60)
for f in all_files:
    n1 = replace_in_file(f, "In-line Raman", "At-line Raman")
    n2 = replace_in_file(f, "in-line Raman", "at-line Raman")
    n3 = replace_in_file(f, "Inline Raman", "At-line Raman")
    n4 = replace_in_file(f, "inline Raman", "at-line Raman")
    n5 = replace_in_file(f, "in-situ Raman", "at-line Raman")
    n = n1 + n2 + n3 + n4 + n5
    if n > 0:
        print(f"  {f.name}: {n} replacements")
        total_changes += n

print()
print("=" * 60)
print("CHANGE 6: Sand mill/milling → Bead mill/milling")
print("=" * 60)
for f in all_files:
    n1 = replace_in_file(f, "Sand Milling", "Bead Milling")
    n2 = replace_in_file(f, "Sand milling", "Bead milling")
    n3 = replace_in_file(f, "sand milling", "bead milling")
    n4 = replace_in_file(f, "sand mill ", "bead mill ")
    n5 = replace_in_file(f, "Sand mill ", "Bead mill ")
    n6 = replace_in_file(f, "sand mill)", "bead mill)")
    n7 = replace_in_file(f, "sand mill,", "bead mill,")
    n8 = replace_in_file(f, "Sand mill |", "Bead mill |")
    n9 = replace_in_file(f, "sand mill |", "bead mill |")
    n10 = replace_in_file(f, "**sand mill**", "**bead mill**")
    # Also handle "Horizontal bead mill (sand mill)" pattern
    n11 = replace_in_file(f, "(sand mill)", "(bead mill)")
    n = n1+n2+n3+n4+n5+n6+n7+n8+n9+n10+n11
    if n > 0:
        print(f"  {f.name}: {n} replacements")
        total_changes += n

print()
print("=" * 60)
print("CHANGE 10: CFO → Financial Team / GHG Team")
print("=" * 60)
for f in all_files:
    # GHG-specific CFO references → GHG team
    n1 = replace_in_file(f, "GHG calculator by CFO team", "GHG calculator by GHG team")
    n2 = replace_in_file(f, "GHG calculator by CFO", "GHG calculator by GHG team")
    # General CFO → Financial Team
    n3 = replace_in_file(f, "CFO TEAM", "FINANCIAL TEAM")
    n4 = replace_in_file(f, "CFO team", "Financial Team")
    n5 = replace_in_file(f, "CFO/finance team", "Financial Team")
    n6 = replace_in_file(f, "CFO", "Financial Team")  # catch remaining
    n = n1+n2+n3+n4+n5+n6
    if n > 0:
        print(f"  {f.name}: {n} replacements")
        total_changes += n

print()
print("=" * 60)
print("CHANGE 4: FIB-Eni JV → ESS JV")
print("=" * 60)
# First pass: full name "FIB-Eni joint venture" → "ESS (Eni Storage Systems) JV"
# We'll do first-mention expansion manually per file, rest as "ESS JV"
for f in md_files:
    with open(f, 'r') as fh:
        content = fh.read()

    changed = False
    # Replace "FIB-Eni Joint Venture" (heading case) with expanded first
    if "FIB-Eni Joint Venture" in content:
        content = content.replace("FIB-Eni Joint Venture", "ESS (Eni Storage Systems) JV", 1)
        content = content.replace("FIB-Eni Joint Venture", "ESS JV")
        changed = True
    # Replace "FIB-Eni joint venture"
    if "FIB-Eni joint venture" in content:
        content = content.replace("FIB-Eni joint venture", "ESS (Eni Storage Systems) JV", 1)
        content = content.replace("FIB-Eni joint venture", "ESS JV")
        changed = True
    # Replace "FIB-Eni JV"
    if "FIB-Eni JV" in content:
        # Only expand if no expansion already done in this file
        if "ESS (Eni Storage Systems) JV" not in content:
            content = content.replace("FIB-Eni JV", "ESS (Eni Storage Systems) JV", 1)
        content = content.replace("FIB-Eni JV", "ESS JV")
        changed = True

    if changed:
        with open(f, 'w') as fh:
            fh.write(content)
        count = content.count("ESS JV") + content.count("ESS (Eni Storage Systems) JV")
        print(f"  {f.name}: updated ({count} ESS JV references)")
        total_changes += count

print()
print("=" * 60)
print("CHANGE 3: Technology licensor → Youshan")
print("=" * 60)
youshan_full = "Zhejiang Youshan New Material Technology Co., LTD."
for f in all_files:
    with open(f, 'r') as fh:
        content = fh.read()

    changed = False
    # Replace [TO BE COMPLETED: technology licensor name]
    if "[TO BE COMPLETED: technology licensor name]" in content:
        content = content.replace("[TO BE COMPLETED: technology licensor name]", youshan_full)
        changed = True
    if "[TO BE COMPLETED: Technology licensor name]" in content:
        content = content.replace("[TO BE COMPLETED: Technology licensor name]", youshan_full)
        changed = True

    # Replace "the project's technology licensor" with named version (first mention expanded)
    if "project's technology licensor" in content:
        content = content.replace(
            "project's technology licensor",
            f"project's technology licensor, {youshan_full} (hereafter 'Youshan')",
            1
        )
        # Subsequent mentions: just replace "technology licensor" context-sensitively
        changed = True

    # Replace generic "Technology Licensor" in tables
    if "| Technology Licensor |" in content and youshan_full not in content.split("| Technology Licensor |")[0]:
        content = content.replace("| Technology Licensor |", f"| Technology Licensor (Youshan) |")
        changed = True

    if changed:
        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  {f.name}: updated with Youshan")
        total_changes += 1

print()
print("=" * 60)
print("CHANGE 7: Brindisi coordinates 41.0N, 17.9E → 40.615°N, 17.980°E")
print("=" * 60)
for f in all_files:
    n = replace_in_file(f, "41.0N, 17.9E", "40.615°N, 17.980°E")
    if n > 0:
        print(f"  {f.name}: {n} replacements")
        total_changes += n

# Also add the detailed description in the main location sections
for f in [DRAFTS / "00_project_and_applicants.md", DRAFTS / "annex_feasibility_study.md"]:
    with open(f, 'r') as fh:
        content = fh.read()

    # Add Eni Rewind description near coordinates if not already present
    if "Punta della Contessa" not in content and "40.615" in content:
        content = content.replace(
            "40.615°N, 17.980°E",
            "40.615°N, 17.980°E), located just south of the city near the industrial port area and Punta della Contessa, within the broader multi-company petrochemical hub (Versalis, Enipower, Basell) managed by Eni Rewind for soil and groundwater remediation. The site includes an Enipower combined-cycle power plant facing the Adriatic Sea",
            1
        )
        # Clean up the double closing paren if needed
        content = content.replace("°E))", "°E)")
        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  {f.name}: added detailed site description")
        total_changes += 1

print()
print("=" * 60)
print("CHANGE 8: Add Teverola FIB/FAAM Li-ion site")
print("=" * 60)
# Add to 00_project_and_applicants.md after FIB description
f = DRAFTS / "00_project_and_applicants.md"
with open(f, 'r') as fh:
    content = fh.read()

if "Teverola" not in content:
    # Find the FIB/FAAM description section and add Teverola info
    teverola_text = " FIB's existing Li-ion cell manufacturing operations are based at the Teverola site (Teverola 1 and Teverola 2 plants) in the Province of Caserta, Campania, near Naples."
    # Insert after the first mention of FIB's founding/employees
    if "354 employees" in content:
        content = content.replace(
            "354 employees",
            "354 employees." + teverola_text,
            1
        )
        # Clean up double period
        content = content.replace("..", ".")
        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  00_project_and_applicants.md: added Teverola site info")
        total_changes += 1

# Also add to feasibility study
f = DRAFTS / "annex_feasibility_study.md"
with open(f, 'r') as fh:
    content = fh.read()

if "Teverola" not in content:
    if "354 employees" in content:
        teverola_text = " FIB operates two existing Li-ion cell manufacturing plants (Teverola 1 and Teverola 2) at its Teverola site in the Province of Caserta, Campania (near Naples), providing direct experience in lithium battery production at industrial scale."
        content = content.replace(
            "354 employees",
            "354 employees." + teverola_text,
            1
        )
        content = content.replace("..", ".")
        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  annex_feasibility_study.md: added Teverola site info")
        total_changes += 1

print()
print("=" * 60)
print("CHANGE 2: FREYR plans cancelled")
print("=" * 60)
freyr_replacements = {
    # Past tense the FREYR references
    "FREYR's funded project targets": "FREYR had targeted",
    "FREYR's funded but not-yet-operational project in Finland": "FREYR's now-cancelled project in Finland (originally funded but subsequently abandoned)",
    "FREYR Battery (Finland)**: Received a EUR 122M Innovation Fund grant (October 2024) for a planned 30,000 t/yr LFP CAM facility in Vaasa, Finland": "FREYR Battery (Finland)**: Had received a EUR 122M Innovation Fund grant (October 2024) for a planned 30,000 t/yr LFP CAM facility in Vaasa, Finland, but subsequently cancelled these plans, citing a strategic pivot to the US market (Giga America)",
    "FACE and FREYR together would establish a two-node European LFP CAM supply base": "Following FREYR's cancellation, FACE would be the sole European LFP CAM production facility",
    "providing geographic diversification within the EU LFP supply landscape alongside FREYR's Northern European site": "becoming the sole European LFP CAM production facility following FREYR's cancellation of its Vaasa plans",
    "complementing FREYR's Northern European site (Vaasa, Finland) and ensuring Mediterranean access": "becoming the sole European LFP CAM production facility following FREYR's cancellation of its Vaasa plans, providing Mediterranean access",
    "The Innovation Fund has not funded LFP CAM pilots — it has funded a production-scale facility (FREYR, EUR 122M).": "The Innovation Fund had previously funded FREYR's 30,000 t/yr facility (EUR 122M), but FREYR subsequently cancelled these plans. FACE would now be the sole Innovation Fund-supported LFP CAM production facility in Europe.",
    "This exceeds the comparable FREYR project (30,000 t/yr [SRC-025]) and positions": "With FREYR's cancellation of its 30,000 t/yr project [SRC-025], this positions",
    "This exceeds the comparable FREYR project (30,000 t/yr [SRC-025]).": "With FREYR's cancellation of its 30,000 t/yr project [SRC-025], the Brindisi facility would be the only planned LFP CAM plant in Europe.",
}

for f in md_files:
    with open(f, 'r') as fh:
        content = fh.read()

    changed = False
    for old, new in freyr_replacements.items():
        if old in content:
            content = content.replace(old, new)
            changed = True

    if changed:
        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  {f.name}: FREYR references updated to cancelled")
        total_changes += 1

print()
print("=" * 60)
print("CHANGE 9: Scale justification kiln data (01_innovation.md)")
print("=" * 60)
f = DRAFTS / "01_innovation.md"
with open(f, 'r') as fh:
    content = fh.read()

if "rotary hearth kilns exceeding 110 m" not in content:
    # Find "Why This Scale Is Most Appropriate" section
    scale_marker = "Why This Scale Is Most Appropriate"
    if scale_marker in content:
        # Find a good insertion point after the existing scale arguments
        # Insert the licensor kiln data as supporting evidence
        kiln_data = """
**Industrial calcination scale evidence from licensor candidates**: Information provided by licensor candidates confirms that industrial calcination processes for cathode active materials inherently benefit from scale. The evolution from 5x3 to next-generation 6x3 rotary hearth kilns exceeding 110 m in length, with capacities reaching up to 25 kton per year per unit, reflects a clear trend toward larger, more integrated systems. These kilns operate with high throughput (up to 620 saggers per hour), multi-row and multi-layer configurations, and continuous operation without shutdown for maintenance. The ability to maintain stringent process conditions — ultra-low oxygen levels (<1 ppm), tight thermal uniformity (+/-10 C), and precise mechanical control of saggar movement — demonstrates that process stability and product quality are achieved through centralised control systems that become more efficient when distributed over higher production volumes. The reduction in specific operating costs (~414 RMB per ton at ~19 kton/year scale) and the consolidation of capacity into fewer, higher-throughput kilns (4 kilns enabling ~50 kton/year plants) illustrate clear economies of scale. These elements confirm that the performance, energy efficiency, and economic viability of LFP calcination are not scale-neutral, but improve significantly as production systems increase in size and throughput.

"""
        # Insert after the "Why This Scale" heading area
        # Find the next section heading after it
        idx = content.index(scale_marker)
        # Find the end of the existing scale section (next ## or ### heading)
        next_section = content.find("\n## ", idx + len(scale_marker))
        next_subsection = content.find("\n### ", idx + len(scale_marker))
        if next_subsection > 0 and (next_section < 0 or next_subsection < next_section):
            insert_point = next_subsection
        elif next_section > 0:
            insert_point = next_section
        else:
            insert_point = len(content)

        content = content[:insert_point] + kiln_data + content[insert_point:]

        with open(f, 'w') as fh:
            fh.write(content)
        print(f"  01_innovation.md: added kiln scale data")
        total_changes += 1

print()
print("=" * 60)
print(f"TOTAL CHANGES: {total_changes}")
print("=" * 60)

# Also update the abstract temperature if present
f = DRAFTS / "abstract.md"
with open(f, 'r') as fh:
    content = fh.read()
n = 0
for old, new in [("650-700", "700-800"), ("600-700", "700-800")]:
    c = content.count(old)
    if c > 0:
        content = content.replace(old, new)
        n += c
if n > 0:
    with open(f, 'w') as fh:
        fh.write(content)
    print(f"  abstract.md: {n} temperature fixes")

# Update 02_3_dnsh.md temperature too
f = DRAFTS / "02_3_dnsh.md"
with open(f, 'r') as fh:
    content = fh.read()
for old, new in [("650-700", "700-800"), ("600-700", "700-800")]:
    content = content.replace(old, new)
with open(f, 'w') as fh:
    fh.write(content)
print("  02_3_dnsh.md: temperature check done")

print("\nDone! Run regenerate_meta.py and combine_to_docx.py next.")
