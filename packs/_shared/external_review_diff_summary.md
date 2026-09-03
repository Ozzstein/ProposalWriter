## External Review — Round {ROUND} Complete

| Outcome | Count |
|---------|-------|
| Resolved | {RESOLVED} |
| Deferred (next round) | {DEFERRED} |
| Rejected (with rationale) | {REJECTED} |
| Stale (needs manual review) | {STALE} |

### Files changed
{FILES_CHANGED}

### New sources added (SRC-xxx)
{NEW_SOURCES}

### Claims updated (CLM-xxx)
{UPDATED_CLAIMS}

### Stale items requiring manual review
{STALE_ITEMS}

---

**Next steps:**
- If more reviewer files to process: drop them in `inputs/reviews/round{NEXT_ROUND}/` and run `/external-review --new-round`
- If all rounds complete: run `/gate-check external-feedback` to verify closure
- If ready to resubmit: run `/gate-check submission`
