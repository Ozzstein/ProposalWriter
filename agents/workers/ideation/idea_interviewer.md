# Idea Interviewer

**Not a spawned worker.** Like `bp_interviewer`, this file is a protocol + question bank that the Ideation Orchestrator reads and executes directly in the main conversation — spawned agents cannot interact with the user. No `.claude/agents/` stub is generated for it.

## Mission
Turn a raw, possibly vague project idea into 2–3 sharply stated candidate framings that can be probed against prior art. Extract what the user actually knows, expose what they don't, and never let a fuzzy answer pass as a firm one.

## Ground Rules

- Ask **one batch at a time**; wait for answers before the next batch.
- Record answers verbatim in the interview notes — do not paraphrase away specifics.
- When an answer is vague ("it's more efficient", "nobody does this"), probe once: ask for the number, the mechanism, or the name of the closest competitor. If still vague, record it as an **open question**, not a fact.
- Do not suggest novelty claims to the user — elicit theirs, then stress-test in Phase 2/3.
- Skip questions the user has already answered in `context.md` or earlier conversation; confirm rather than re-ask.
- The user may not know an answer — that is a finding, not a failure. Mark it `[UNKNOWN]`.

## Question Batches

### Batch 1 — The problem
| key | question |
|---|---|
| problem.statement | What problem are you solving? Who has this problem, concretely? |
| problem.cost | What does the problem cost today (money, time, emissions, lives, throughput)? How do you know? |
| problem.current_best | How is it handled today, and what's the best existing solution's biggest limitation? |

### Batch 2 — The idea
| key | question |
|---|---|
| idea.mechanism | What is your approach, mechanically? What does it *do* that current solutions don't? |
| idea.why_now | Why is this possible now when it wasn't five years ago (new data, method, hardware, regulation)? |
| idea.evidence | What evidence do you already have that it works (prior results, pilot, publication, simulation)? |

### Batch 3 — Novelty
| key | question |
|---|---|
| novelty.claim | Complete the sentence: "We are the first / only / best at ___." |
| novelty.closest | Who or what is closest to doing this already? (Name names — groups, companies, projects.) |
| novelty.fear | What existing work are you most afraid a reviewer will point to and say "this already exists"? |

### Batch 4 — Fit and ambition
| key | question |
|---|---|
| fit.funder | Which funder/call do you have in mind, if any? (Determines scoring lens: excellence vs impact vs GHG.) |
| fit.maturity | Where is the idea today — concept, lab result, prototype, pilot (rough TRL)? |
| fit.team | Does your team have the capabilities the idea needs? Which are missing? |
| ambition.outcome | If it works, what measurable outcome will you claim in 3–5 years (with numbers)? |

## Output of the Interview

After the batches, the orchestrator synthesizes **2–3 candidate framings** — distinct fundable angles on the same idea (e.g. same technology framed against different gaps, novelty types, or calls). Each framing gets:
- a one-sentence statement (the would-be hypothesis)
- the mechanism in 2–3 sentences
- a claimed novelty type (first / only / best / combination / scale / application)
- the target gap it addresses

Present the framings to the user for correction **before** any prior-art probes are spawned. The corrected framings and the verbatim interview notes go into the Phase 2/3 inputs.
