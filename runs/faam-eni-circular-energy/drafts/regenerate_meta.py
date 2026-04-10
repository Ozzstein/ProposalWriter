#!/usr/bin/env python3
"""Regenerate all _meta.json files from actual draft content."""

import json
import re
import os
from pathlib import Path

DRAFTS_DIR = Path(__file__).parent

SECTION_NAMES = {
    "abstract": "Abstract",
    "00_project_and_applicants": "Section 0: Project and Applicants",
    "01_innovation": "Section 1: Degree of Innovation",
    "02_3_dnsh": "Section 2.3: DNSH Minimum Requirements",
    "03_1_technical_maturity": "Section 3.1: Technical Maturity",
    "03_3_operational_maturity": "Section 3.3: Operational Maturity",
    "03_4_risk_management": "Section 3.4: Risk Management",
    "04_replicability": "Section 4: Replicability",
    "06_bonus": "Section 6: Bonus Points",
    "07_workplan": "Section 7: Workplan",
    "08_09_other_declarations": "Sections 8-9: Other and Declarations",
    "annex_feasibility_study": "Annex: Feasibility Study",
}


def extract_meta_from_draft(md_path):
    """Extract claims, sources, assumptions, open issues from draft text."""
    with open(md_path, 'r') as f:
        text = f.read()

    # Extract unique CLM-XXX references
    claim_ids = sorted(set(re.findall(r'CLM-\d+', text)))

    # Extract unique SRC-XXX references (including SRC-ED-XXX, SRC-PAT-XXX, SRC-DT-XXX)
    source_ids = sorted(set(re.findall(r'SRC-(?:[A-Z]+-)*\d+', text)))

    # Extract [TO BE COMPLETED: ...] items
    to_be_completed = re.findall(r'\[TO BE COMPLETED[:\s]*([^\]]*)\]', text)

    # Extract [ASSUMPTION: ...] items
    assumptions = re.findall(r'\[ASSUMPTION[:\s]*([^\]]*)\]', text)

    # Combine as open issues
    open_issues = []
    for item in to_be_completed:
        open_issues.append(f"TO BE COMPLETED: {item.strip()}")
    for item in assumptions:
        open_issues.append(f"ASSUMPTION: {item.strip()}")

    # Word count
    word_count = len(text.split())

    # Character count (for abstract)
    char_count = len(text)

    return {
        "claim_ids": claim_ids,
        "source_ids": source_ids,
        "assumptions_used": assumptions,
        "open_issues": open_issues,
        "word_count": word_count,
        "character_count": char_count,
    }


def main():
    updated = 0
    for md_file in DRAFTS_DIR.glob("*.md"):
        stem = md_file.stem
        if stem in ("combine_to_docx", "regenerate_meta"):
            continue

        meta_path = DRAFTS_DIR / f"{stem}_meta.json"
        section_name = SECTION_NAMES.get(stem, stem)

        extracted = extract_meta_from_draft(md_file)

        # Load existing meta if present (preserve any fields we don't extract)
        existing = {}
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                existing = json.load(f)

        # Build new meta
        new_meta = {
            "section_name": section_name,
            "target_audience": existing.get("target_audience", "Innovation Fund industrial/policy evaluators"),
            "claim_ids": extracted["claim_ids"],
            "source_ids": extracted["source_ids"],
            "assumptions_used": extracted["assumptions_used"],
            "open_issues": extracted["open_issues"],
            "word_count": extracted["word_count"],
        }

        # Add character count for abstract
        if stem == "abstract":
            new_meta["character_count"] = extracted["character_count"]

        with open(meta_path, 'w') as f:
            json.dump(new_meta, f, indent=2)

        updated += 1
        print(f"Updated: {meta_path.name}")
        print(f"  Claims: {len(extracted['claim_ids'])}, Sources: {len(extracted['source_ids'])}, "
              f"Open issues: {len(extracted['open_issues'])}, Words: {extracted['word_count']}")

    print(f"\nRegenerated {updated} meta files.")


if __name__ == '__main__':
    main()
