> Implemented: priorities 1 and 2 (call ingestion before ideation, intake scope configuration) —
> see `docs/superpowers/specs/2026-09-03-intake-scope-design.md`.

# ProposalWriter: Recommended Workflow and Agent Architecture

## Executive assessment

ProposalWriter has a solid technical foundation, but its workflow is too linear and its roster of 32 agent contracts is unnecessarily fragmented.

The recommended redesign has four principles:

1. Ingest the call before generating or refining ideas.
2. Use iterative, user-approved loops for ideation, research, drafting, and feedback.
3. Replace narrow section-specific agents with a smaller set of reusable capability agents.
4. Use a hybrid architecture: application-managed gates and state, with Claude Agent SDK subagents performing bounded, parallel work inside each stage.

The target should be a proposal system that adapts to any call through configuration, evidence mapping, and dynamic task briefs rather than through a growing collection of specialised agents.

## Recommended workflow

```text
Call ingestion
  -> Qualification and scope configuration
  -> Ideation and research loop
  -> Approved concept brief
  -> Proposal blueprint
  -> Evidence coverage loop
  -> Drafting and optional production branches
  -> Integrated draft
  -> Internal review and revision loop
  -> External feedback loop
  -> Final submission gate
  -> Export
```

## 1. Ingest the call before ideation

For a call-specific proposal, ideation should begin only after the call has been analysed.

Call ingestion should extract:

- Eligibility conditions and disqualifiers
- Evaluation criteria and scoring weights
- Required sections, forms, and annexes
- Technical scope, expected outcomes, and impact requirements
- TRL, geography, consortium, duration, and deadline constraints
- Budget and financial requirements
- Business-plan and exploitation requirements
- Page, word, format, and submission restrictions

This ensures that the system develops a fundable response to the opportunity rather than generating an interesting but potentially unsuitable idea.

If there is no target call, the system can use an exploratory mode. Ideas generated in that mode should be identified as preliminary and should undergo call alignment later.

## 2. Add scope configuration at intake

After call ingestion, the user should decide which optional components to include.

```text
Finance: excluded / included / required
Business plan: excluded / included / required
Figures: excluded / included / required
External review: excluded / included / required
```

The states mean:

- `excluded`: not requested by the user and not required by the call.
- `included`: requested by the user or accepted after a system recommendation.
- `required`: mandatory under the call and therefore cannot be skipped.

The governing rule is:

> User preference controls optional work. Call requirements control mandatory work.

Finance and business planning must remain separate:

- Finance covers budgets, costs, funding requirements, cash flow, assumptions, and financial narratives.
- Business planning covers markets, customers, business models, commercialisation, exploitation, and sustainability.

The user may therefore include finance without a business plan or include a business plan without a detailed financial model.

## 3. Make ideation iterative and user-approved

Ideation should be a loop rather than a single stage.

```text
Initial idea
  -> Targeted research
  -> State-of-the-art analysis
  -> Gap and opportunity identification
  -> Idea and angle refinement
  -> User review
       -> not satisfied: research, redirect, or refine again
       -> satisfied: approve concept brief
```

Each iteration should determine whether the idea is:

- Aligned with the call
- Meaningfully differentiated
- Supported by a real, evidenced gap
- Feasible within the available resources
- Capable of producing persuasive and measurable impact

At every checkpoint, the user should be able to:

- `Change direction`: explore a different problem or solution.
- `Deepen evidence`: investigate literature, patents, competitors, markets, or feasibility.
- `Strengthen the angle`: improve novelty, methodology, scope, impact, or positioning.
- `Approve`: freeze the concept and proceed.

The approved concept brief should contain:

- Problem and beneficiaries
- State-of-the-art baseline
- Evidence-backed gap
- Core idea and angle of attack
- Proposed method and outcomes
- Alignment with call criteria
- Initial implementation approach
- Risks, assumptions, and unresolved evidence needs

The approved concept brief becomes the strategic source of truth. Downstream agents must not silently change it. Material changes must explicitly reopen the concept loop and require user approval.

## 4. Create a proposal blueprint before drafting

After concept approval, the system should build a proposal blueprint.

For each call criterion and required section, the blueprint should specify:

- The argument or claim that must be established
- The evidence required
- The relevant section
- Dependencies on partners, figures, finance, or business planning
- User inputs still needed
- Acceptance criteria for drafting and review

```text
Call criterion
  -> Required argument
  -> Proposal section
  -> Supporting evidence
  -> Drafting instructions
  -> Reviewer test
```

Completeness should mean that every scoring criterion is persuasively addressed, not merely that every section contains text.

## 5. Make research coverage-driven

Research should be driven by the blueprint and evidence gaps, not by source counts alone.

The research gate should verify that:

- Every evaluation criterion has sufficient supporting evidence.
- Every major claim is supported or explicitly marked as an assumption.
- State-of-the-art, novelty, market, and competitor claims are evidenced.
- Sources are appropriate, credible, current, and traceable.
- Contradictory evidence has been considered.
- Remaining evidence gaps are resolved, disclosed, or escalated.
- Evidence is assigned to the section and claim where it will be used.

A large evidence library should not compensate for weak support of an important evaluation criterion.

## 6. Streamline the agent roster

The current 32 contracts are too granular. They increase orchestration overhead, duplicate responsibilities, and make the system harder to maintain and adapt.

The recommended roster is eight core capability agents and two conditional specialists.

| Agent | Responsibility |
|---|---|
| Call analyst | Call parsing, eligibility, requirements, and evaluation criteria |
| Strategy lead | Ideation loop, positioning, call alignment, and concept brief |
| Research analyst | Evidence collection, state of the art, patents, competitors, novelty, and gaps |
| Proposal architect | Blueprint, criterion mapping, dependencies, and section briefs |
| Proposal writer | Drafting any narrative section from structured instructions |
| Technical/evidence reviewer | Credibility, novelty, feasibility, citations, and claim support |
| Evaluator/compliance reviewer | Scoring, compliance, completeness, format, and persuasiveness |
| Revision editor | Applying feedback, maintaining consistency, and initiating re-review |
| Finance specialist | Conditional finance modelling, narrative, and review |
| Business specialist | Conditional market, exploitation, and business-plan work |

Current narrow agents should be consolidated as follows:

- Literature search, web search, and patent scanning become Research Analyst tools or modes.
- State-of-the-art synthesis, novelty mapping, and gap analysis become Research Analyst outputs.
- Abstract, excellence, impact, implementation, and other narrative writers become one Proposal Writer.
- Scientific and adversarial review become Technical/Evidence Reviewer modes.
- Compliance checking becomes part of the Evaluator/Compliance Reviewer.
- Feedback parsing and application become Revision Editor functions.
- Plotting and image generation become tools invoked when figures are included.
- Normal workflow progression becomes deterministic application logic rather than requiring a planning agent.

The system can still create temporary subagents for parallel tasks. Those temporary workers do not need to become permanent agent identities.

## 7. Use a hybrid Claude Agent SDK architecture

The current system uses the Claude Agent SDK for agent execution but uses custom application logic for orchestration. This is appropriate for proposal development and should be retained in a more deliberate hybrid design.

A fully SDK-native hierarchy would allow a lead Claude agent to decide which subagents to invoke, how to divide the work, and when to proceed. This offers strong flexibility but should not control mandatory proposal obligations.

The recommended architecture is:

```text
Application-managed workflow
  -> owns authoritative state, scope, gates, approvals, and stage transitions

Claude capability agent
  -> reasons and plans within the currently approved stage

SDK-native subagents or dynamic workflows
  -> perform bounded parallel tasks within that stage

Application validator
  -> validates, persists, and approves results before progression
```

### Responsibilities retained by the application

The application should control:

- Eligibility and qualification rules
- Required and excluded modules
- User approval checkpoints
- Concept approval, freezing, and reopening
- Criterion and section completion tracking
- Evidence coverage gates
- Required review stages
- Authoritative project state
- Final submission and export permission
- Recovery and resumption after failures

These operations should not depend on an orchestrating model remembering or choosing to perform them.

### Responsibilities suitable for SDK-native subagents

Native subagents or dynamic workflows are valuable for:

- Parallel literature, patent, market, and competitor research
- Independent verification of important claims
- Exploring alternative ideas or angles
- Drafting independent sections from an approved blueprint
- Reviewing sections from different evaluator perspectives
- Finding contradictions across evidence and proposal claims
- Processing large numbers of reviewer comments
- Running adversarial verification or fact-checking passes

For example:

```text
Application opens Research stage
  -> Research Analyst creates evidence tasks
  -> SDK subagents investigate tasks in parallel
  -> Research Analyst synthesises findings
  -> Application checks criterion-level evidence coverage
  -> Uncovered criteria trigger another research cycle
```

### Why the hybrid approach is preferable

| Concern | Application-managed layer | SDK-native layer |
|---|---|---|
| Mandatory obligations | Deterministically enforced | Not responsible |
| User approvals | Persisted and resumable | Participates when requested |
| Call adaptability | Driven by configuration | Handles unexpected analytical work |
| Parallelism | Defines safe boundaries | Executes parallel tasks |
| State consistency | Maintains source of truth | Returns validated outputs |
| Auditability | Records gates and decisions | Records reasoning and evidence |
| Cost control | Sets budgets and concurrency | Uses resources within those limits |
| Failure recovery | Resumes known workflow state | Reruns only affected bounded tasks |

This combines predictable proposal governance with the flexibility of native multi-agent reasoning.

## 8. Keep agent count separate from execution count

The number of permanent agent definitions and the number of runtime subagents are different architectural decisions.

The system can maintain ten reusable capability definitions while spawning multiple temporary instances of them. For example, one Research Analyst capability could create six parallel research tasks without requiring six permanent specialist agents.

This produces flexibility without clutter:

```text
Stable capability roster
  + call-specific task definitions
  + temporary parallel SDK subagents
  = adaptable multi-agent execution
```

## 9. Treat optional modules as production branches

Finance, business planning, and figures should branch from the approved blueprint and rejoin before review.

```text
Approved blueprint
  -> Narrative drafting
  -> Finance branch, when included or required
  -> Business branch, when included or required
  -> Figures branch, when included or required
  -> Integration gate
  -> Complete first draft
```

The integration gate should verify that:

- Budget figures match the work plan and timeline.
- Financial assumptions agree with the narrative.
- Business claims agree with the impact and market sections.
- Figures support the proposal’s actual argument.
- Cross-references and annex references are valid.

No draft should proceed while a required branch is incomplete.

## 10. Separate compliance review from evaluator review

The first review pass should verify structure and compliance:

- Eligibility and administrative conditions
- Required sections, annexes, and forms
- Page and word limits
- Template and submission requirements
- Criterion coverage
- Required finance, business, figures, and attachments

The second pass should simulate evaluation:

- Technical or scientific credibility
- Novelty and differentiation
- Feasibility
- Implementation quality
- Impact and exploitation
- Budget credibility, when applicable
- Evidence quality, clarity, and persuasiveness

Revision and re-scoring should continue until the required threshold is met or an unresolved decision is escalated to the user.

## 11. Make feedback reopen affected stages

External feedback should reopen the relevant part of the workflow.

```text
Feedback ingestion
  -> Comment classification
  -> Affected claim and section identification
  -> Targeted research, if necessary
  -> Targeted revision
  -> Targeted re-review
  -> Submission gate recheck
  -> Resolution
```

A comment should be marked resolved only after the resulting change passes the relevant review gate.

A novelty challenge should reopen research and technical review. A budget challenge should reopen finance and corresponding narrative sections. A strategic challenge may need to reopen the concept brief with user approval.

## 12. Keep export as the final controlled step

Export should be available only when:

- All mandatory sections and annexes exist.
- Required production branches are complete.
- All evaluation criteria are covered.
- No high-priority review findings remain unresolved.
- External feedback has been addressed and re-reviewed.
- Compliance and submission gates pass.
- The output matches the required template and format.

## Claude Agent SDK conformance recommendations

The system can accurately be described as:

> A proposal-writing workflow engine built on the Claude Agent SDK, using application-managed orchestration and bounded SDK-native agent workflows.

Developers should also:

- Pin and test a supported Claude Agent SDK version.
- Add integration tests for one-shot calls, sessions, structured output, tools, hooks, and subagent workflows.
- Update or archive documentation describing agents spawning subagents where this contradicts the implemented architecture.
- Define explicit limits for subagent concurrency, depth, token cost, retries, and allowed tools.
- Validate every subagent output before it enters authoritative project state.
- Record which agent, task brief, evidence inputs, model version, and workflow version produced each important artifact.

## Priority changes

1. Move call ingestion before ideation.
2. Add intake scope configuration.
3. Implement the user-approved concept refinement loop.
4. Introduce the proposal blueprint and criterion-to-evidence map.
5. Replace source-count gates with evidence-coverage gates.
6. Consolidate 32 contracts into reusable capability agents.
7. Retain application-managed stage control and add bounded SDK-native parallelism within stages.
8. Add mandatory branch rejoin points.
9. Make feedback trigger targeted revision and re-review.
10. Restrict export until every submission gate passes.

## Core design principle

The system should optimise for a proposal that is strategically aligned, evidence-backed, internally consistent, and demonstrably responsive to the call’s scoring criteria.

The application should guarantee that required work happens. Claude agents should provide the reasoning, research, writing, and critique needed to perform that work well.