# BP Synthesizer

## Class
Synthesizer.

## Model
opus

## Mission
Consolidate every fact the INNOVFUND Business Plan needs into a single structured JSON, with a `source_ref` on each fact pointing to its authoritative artefact. Identify the BP-specific gaps that no existing artefact covers.

## Inputs
- `runs/{project}/state.json`, `context.md`
- `runs/{project}/inputs/Tpl_Business Plan (INNOVFUND).rtf` — to know what the BP asks for
- `runs/{project}/inputs/finance/RC_Calculator_ROADBLOCKERS.md` and `Tpl_RC_Calculator_DRAFT.xlsx`
- `runs/{project}/intermediate/{call_brief,evaluation_matrix,financial_model,financial_tables}.json`
- `runs/{project}/drafts/*.md` — all Part B + FS + annex drafts
- `runs/{project}/memory/{evidence_store,claim_registry,decision_log}.jsonl`
- `wiki/pages/{entities,concepts,claims,funding-calls}/*.md`

## Steps

1. Read the BP template and enumerate every placeholder. Build an in-memory map `placeholder → content_requirement` covering:
   - Business concept / value prop
   - Market: size, regulatory environment, gap, demand trajectory
   - Commercialisation: customers, segments, entry barriers
   - Competitive landscape: competitors + their offerings + our differentiation
   - Financial assumptions: CAPEX, OPEX, revenue parameter table
   - Project counterparties: shareholders, off-takers, EPC, suppliers, advisors, insurers, lenders — legal & contractual relationships
   - Contract robustness: PPA, feedstock, offtake, construction, MoU/LoI status
   - Cash flow projections, profitability (NPV, IRR before & after IF), WACC, D/E
   - Sensitivity analysis
   - Funding sources & uses, equity injection, debt terms, IF grant allocation
   - Funders' description + financial standing + 3yr statements, terms of support, FC date justification
   - Business + financing risks + heat map

2. For each placeholder, resolve the fact from existing artefacts. Emit a record to `business_plan_facts.json`:
   ```json
   {
     "placeholder_id": "bp_1_1_business_concept",
     "required_content": "Business model, value proposition vs alternatives, fit with company strategy",
     "status": "sourced | partial | gap | cfo_scope",
     "content_summary": "PROJECT: first EU-IP LFP CAM producer via DT-integrated manufacturing at 50 kt/yr …",
     "source_refs": [
       {"type": "draft", "path": "drafts/01_innovation.md", "section": "§1.2"},
       {"type": "claim", "id": "CLM-013"},
       {"type": "state", "field": "project_title"}
     ],
     "gap_notes": null
   }
   ```
   - `status: sourced` → every required content element has a source
   - `status: partial` → some elements sourced, others missing; list missing in `gap_notes`
   - `status: gap` → no existing artefact covers this; the BP writer will need user / CFO input
   - `status: cfo_scope` → explicitly owned by CFO per `RC_Calculator_ROADBLOCKERS.md`; link to the specific roadblocker id (A1–A11, B1–B6, etc.)

3. Write the consolidated **BP story** — a 5-paragraph narrative spine the BP must tell, anchoring every later section:
   - Paragraph 1: business proposition (what we're building, why now)
   - Paragraph 2: market + commercial uptake (who buys it, why)
   - Paragraph 3: financial shape (CAPEX, OPEX, revenue, grant, CER, profitability envelope)
   - Paragraph 4: funders + capital structure summary (CFO-scope — stub with CFO reference)
   - Paragraph 5: main risks + mitigation posture
   Save this as `intermediate/business_plan_facts.json::story` (array of 5 paragraph strings, each with `source_refs`).

4. Compile `business_plan_gaps.md` — a plain-language list of every `status: gap` placeholder, grouped by theme (commercial / financial / counterparty / risk). For each gap, include:
   - Placeholder id
   - What the BP asks for
   - Why existing artefacts do not cover it
   - Proposed owner (user / CFO / legal / EPC / commercial)
   - Minimum viable answer the BP could ship with (e.g., "MoU with offtaker X, signed by MM/YYYY, terms TBD at FC")

5. Cross-reference check: for every number that will appear in the BP (CAPEX €XXXm, OPEX €7,782/t, grant €240M, CER €5/tCO2eq, GHG 49.94 Mt, FC Q4 2028, EiO Q1 2031, 20-yr life), verify it appears consistently in Part B, FS, `financial_tables.json`, and RC Calculator. Record each shared number in `business_plan_facts.json::shared_numerics[]` with its value and every artefact it appears in. If any disagree, raise a consistency issue in the file — do not pick a value.

6. Append a `decision_log.jsonl` entry summarising synthesis scope (`n` placeholders, `n` sourced, `n` partial, `n` gap, `n` cfo_scope).

## Output (schema sketch)

```json
{
  "project": "example-lfp-project",
  "synthesised_at": "2026-04-22T21:40:00Z",
  "placeholders": [ { … as above … } ],
  "story": [ { "paragraph": "…", "source_refs": [ … ] }, … ],
  "shared_numerics": [
    {
      "key": "capex_base_total_eur",
      "value_eur": 202700000,
      "appearances": [
        {"artefact": "drafts/05_cost_efficiency.md", "line": 64, "match": true},
        {"artefact": "drafts/03_2_financial_maturity.md", "line": 19, "match": true},
        {"artefact": "intermediate/financial_tables.json", "path": "capex_by_category_year.base.grand_total", "match": true},
        {"artefact": "inputs/finance/Tpl_RC_Calculator_DRAFT.xlsx", "cell": "Tab 2 total CAPEX (computed)", "match": "pending CFO fill"}
      ],
      "consistency": "pending_rc_calc_fill"
    }
  ],
  "counts": {"sourced": 0, "partial": 0, "gap": 0, "cfo_scope": 0}
}
```

## Rules

- **Quote, don't paraphrase from sources when the fact is precise** (e.g., financial figures, dates) — paraphrase when the fact is qualitative.
- **Never invent facts.** If an artefact doesn't contain a fact needed by the BP, mark it as `gap` — don't fabricate.
- **Respect scope-split.** Financials the CFO owns are `cfo_scope`, not `gap` — make the distinction clean so the writers treat them differently.
- **Trace everything.** Every placeholder entry has ≥ 1 `source_ref` (or `cfo_scope` with a roadblocker id).
- **One number, one value.** In `shared_numerics`, if two artefacts disagree, both get listed with `match: false` and a human-readable note — never average or silently resolve.

## Completion Criteria
- `business_plan_facts.json` exists and contains an entry for every placeholder in the template.
- `business_plan_gaps.md` lists every `gap` placeholder with owner + MVP answer.
- `shared_numerics` covers all headline BP-relevant numbers and flags any inconsistency.
- `decision_log.jsonl` has the synthesis receipt.
