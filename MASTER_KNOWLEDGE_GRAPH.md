# MASTER_KNOWLEDGE_GRAPH

## Graph boundary

This is a domain-neutral conceptual graph made only from the five authorized knowledge artifacts. It maps **Node → Framework → SOP candidate → Prompt candidate → Decision**. Edges indicate conceptual support or use, not proven runtime wiring.

**FACT:** Knowledge atoms, framework IDs, candidate SOPs, candidate prompts, and decision examples exist in the allowed source materials.  
**INFERENCE:** Linking them provides a traceable retrieval path.  
**UNKNOWN:** Whether any linked process is operationally deployed.

## Node → Framework → SOP → Prompt → Decision

| Node | Framework | SOP candidate | Prompt candidate | Decision |
|---|---|---|---|---|
| K-001 Evidence status taxonomy | F-01 FACT / INFERENCE / UNKNOWN | SOP-C01, SOP-C02, SOP-C04 | P-01, P-02, P-05, P-08 | Hold as UNKNOWN when evidence is missing; do not overclaim |
| K-002 Human approval gate | F-02 Human Approval Gate | SOP-C01, SOP-C03, SOP-C05 | P-02, P-03 | Authorize or hold consequential action |
| K-003 Stage separation | F-06 Cognitive Pipeline; F-09 Acceptance State Machine | SOP-C01 | P-02, P-07 | Keep proposal, evaluation, authorization, and action distinct |
| K-004 Evidence before trust | F-03 Evidence Before Trust | SOP-C02 | P-01, P-03, P-04 | Accept only after applicable validation; otherwise revise/reject/hold |
| K-005 Explicit acceptance contract | F-03 Evidence Before Trust | SOP-C01, SOP-C02 | P-02, P-04 | Clarify the claim and criteria before acceptance |
| K-006 Acceptance states | F-09 Acceptance State Machine | SOP-C01, SOP-C02, SOP-C05 | P-02, P-06 | Select accept, revise, reject, or hold |
| K-007 Multidimensional evaluation | F-03 Evidence Before Trust | SOP-C01, SOP-C02 | P-02 | Compare using declared criteria; keep uncalibrated scores advisory |
| K-008 Staged change | F-07 Reversible, Staged Change; F-02 Human Approval Gate | SOP-C01, SOP-C05 | P-02, P-03 | Proceed by bounded stages only after required gates |
| K-009 Audit lineage | F-04 Audit First / Evidence Lineage | SOP-C03, SOP-C04 | P-03, P-08 | Preserve evidence and trace the decision/action |
| K-010 Incident/risk distinction | F-05 Failure Library / Risk–Incident Separation | SOP-C03, SOP-C04, SOP-C05 | P-06, P-08 | Classify as incident, modeled condition, risk, or UNKNOWN |
| K-011 Missing evidence | F-01 FACT / INFERENCE / UNKNOWN; F-09 Acceptance State Machine | SOP-C01, SOP-C02, SOP-C05 | P-01, P-06 | Hold; do not turn absence into pass or failure |
| K-012 Progressive review | F-08 Progressive Evidence Review | SOP-C02, SOP-C04 | P-01, P-04, P-06 | Increase review depth with impact and uncertainty |
| K-013 Preserve invariants | F-07 Reversible, Staged Change | SOP-C06 | P-05 | Preserve reusable controls; quarantine context-bound claims |
| K-014 Verified learning | F-04 Audit First; F-05 Failure Library; F-08 Progressive Evidence Review | SOP-C04 | P-06, P-08 | Update knowledge only after evidence-backed review |
| K-015 Capability vs agent status | F-06 Cognitive Pipeline / Brain Architecture | SOP-C06 | P-07 | Record capability; do not assert an autonomous agent without evidence |

## Edge list

```text
Knowledge Node --grounds--> Framework
Framework --operationalized_as_candidate--> SOP
SOP --elicited_or_reviewed_with--> Prompt
Prompt/SOP --produces_evidence_for--> Decision
Decision --recorded_by--> Audit Node
Audit Node --provides_verified_material_to--> Learning Node
Learning Node --may_refine--> Knowledge Node (INFERENCE; approval needed)
```

## Decision endpoints

- **D-01 Clarify or hold:** K-001, K-005, K-011 → F-01/F-03 → SOP-C01 → P-01/P-02 → hold or clarify.
- **D-02 Accept/revise/reject:** K-004, K-006, K-007 → F-03/F-09 → SOP-C02 → P-02/P-04 → accept, revise, reject, or hold.
- **D-03 Authorize action:** K-002, K-008 → F-02/F-07 → SOP-C01/SOP-C05 → P-02/P-03 → authorize staged action or hold.
- **D-04 Classify failure:** K-005/K-009/K-010/K-011 → F-04/F-05 → SOP-C03 → P-03/P-06 → incident, modeled condition, risk, or UNKNOWN.
- **D-05 Update knowledge:** K-009/K-010/K-014 → F-04/F-05/F-08 → SOP-C04 → P-06/P-08 → proposed reviewed update or no update.
- **D-06 Coordinate capabilities:** K-003/K-015 → F-06/F-09 → SOP-C01/SOP-C06 → P-07 → function handoff; autonomous-agent status remains UNKNOWN.

## Evidence status for edges

**FACT:** The source artifacts provide the node concepts and candidate frameworks/procedures/prompts.  
**INFERENCE:** All cross-layer edges in this graph are a proposed knowledge organization unless the relationship is expressly stated in a source.  
**UNKNOWN:** Runtime execution, automatic edge traversal, ownership, and the receiving graph schema.
