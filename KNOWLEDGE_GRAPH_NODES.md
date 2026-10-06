# KNOWLEDGE_GRAPH_NODES

## Schema

Each atom uses: **ID**, **Title**, **Description**, **Evidence**, **Source**, **Related Atoms**. Type and relationships are listed in the graph index. A node describes a knowledge claim, not necessarily an implemented capability.

- **FACT:** Directly stated in an authorized source.
- **INFERENCE:** Normalized or derived from source statements.
- **UNKNOWN:** Required fields or implementation status not established.

## Nodes

### K-001 — Evidence status taxonomy

- **Type:** Knowledge / epistemic framework
- **Description:** Separate direct fact, reasoned inference, and unsupported or missing information.
- **Evidence:** Sources repeatedly require FACT / INFERENCE / UNKNOWN separation.
- **Source:** `C2_CORE_PRINCIPLES.md` 12, 14; `APEX_CORE_WISDOM.md` 21, 24–25, 50; `C2_COGNITIVE_ARCHITECTURE.md` scope.
- **Related Atoms:** K-002, K-006, K-011, K-014
- **FACT:** The classification is explicit and repeated.
- **INFERENCE:** Use as the provenance/status field for all migrated knowledge.
- **UNKNOWN:** Whether the target has confidence grades beyond this taxonomy.

### K-002 — Human approval gate

- **Type:** Decision framework / strategy
- **Description:** A consequential action requires authorization by a responsible human after evidence and evaluation.
- **Evidence:** Approval and capability gates appear across principles, decision cases, and wisdom.
- **Source:** `C2_CORE_PRINCIPLES.md` 1, 4; `C2_DECISION_GRAPH.md` T3; `APEX_CORE_WISDOM.md` 1, 17, 19.
- **Related Atoms:** K-003, K-004, K-008, K-015
- **FACT:** Human approval is represented as a prerequisite for impact.
- **INFERENCE:** Approval rigor should scale with impact and reversibility.
- **UNKNOWN:** Authority hierarchy and exception process.

### K-003 — Proposal/evaluation/authorization/action separation

- **Type:** Cognitive model / control principle
- **Description:** Keep generating a proposal, assessing it, authorizing it, and acting on it as distinguishable stages.
- **Evidence:** Repeated as a principle and as a cognitive pipeline.
- **Source:** `C2_CORE_PRINCIPLES.md` 4; `C2_COGNITIVE_ARCHITECTURE.md` FACT and pipeline; `C2_META_BRAIN.md` 75–77.
- **Related Atoms:** K-002, K-004, K-005, K-009
- **FACT:** The stages are separated in the documented model.
- **INFERENCE:** Separation helps prevent self-approval and makes handoffs auditable.
- **UNKNOWN:** Whether separate agents/people implement each stage.

### K-004 — Evidence before trust

- **Type:** Verification framework
- **Description:** Validate claims and outputs with provenance, explicit criteria, and suitable checks before relying on them.
- **Evidence:** Verification, independent criteria, and artifact comparison recur.
- **Source:** `C2_CORE_PRINCIPLES.md` 3, 6–8; `C2_DECISION_GRAPH.md` C2, T2, Q1–Q3.
- **Related Atoms:** K-001, K-005, K-006, K-010
- **FACT:** Validation mechanisms are documented.
- **INFERENCE:** Missing checks should hold a decision rather than silently pass it.
- **UNKNOWN:** Complete validation standards.

### K-005 — Explicit acceptance contract

- **Type:** Knowledge / decision criterion
- **Description:** Clarify the request, represent it in a structured form, and state criteria before acceptance or action.
- **Evidence:** The sources describe framing, confirmation, contract validation, and quality criteria.
- **Source:** `C2_CORE_PRINCIPLES.md` 5–7; `C2_DECISION_GRAPH.md` C1, Q1.
- **Related Atoms:** K-003, K-004, K-006, K-012
- **FACT:** Explicit confirmation and declared criteria are included in the decision model.
- **INFERENCE:** Do not infer consent or sufficiency from ambiguous input.
- **UNKNOWN:** Universal field set and adequacy threshold.

### K-006 — Accept / revise / reject / hold

- **Type:** Decision state model
- **Description:** Keep acceptance, repair, rejection, and insufficient-evidence hold as distinct outcomes.
- **Evidence:** Decision Graph and cognitive graph name these outcome states.
- **Source:** `C2_DECISION_GRAPH.md` Q1 and acceptance/rejection gates; `C2_COGNITIVE_GRAPH.md` B4–B5.
- **Related Atoms:** K-001, K-004, K-005, K-008, K-011
- **FACT:** The outcome distinctions are explicit in the sources.
- **INFERENCE:** Every outcome should include rationale and permitted next transition.
- **UNKNOWN:** Retry limits, transition rules, and override policy.

### K-007 — Multidimensional evaluation

- **Type:** Quality framework
- **Description:** Assess alternatives against declared independent criteria and disclose trade-offs.
- **Evidence:** Multi-axis evaluation and uncertainty about thresholds/weights are repeated.
- **Source:** `C2_CORE_PRINCIPLES.md` 7; `C2_DECISION_GRAPH.md` Q1/Q3; `APEX_CORE_WISDOM.md` 6–7, 46–47.
- **Related Atoms:** K-004, K-005, K-006, K-011
- **FACT:** Multidimensional assessment is documented.
- **INFERENCE:** Scores without baseline, weights, or threshold should remain advisory.
- **UNKNOWN:** Criteria values and their calibration.

### K-008 — Staged and reversible change

- **Type:** Strategy / control principle
- **Description:** Limit initial scope, validate in stages, and preserve a recovery path before expanding impact.
- **Evidence:** Staging, bounded scope, sandbox/canary, and rollback are repeated as principles or safeguards.
- **Source:** `C2_CORE_PRINCIPLES.md` 11; `C2_DECISION_GRAPH.md` S3/T3; `APEX_CORE_WISDOM.md` 15–18, 39, 41.
- **Related Atoms:** K-002, K-006, K-009, K-013
- **FACT:** Staging and pre-impact checks are documented as design/mitigation.
- **INFERENCE:** Each stage should have exit, stop, and rollback criteria.
- **UNKNOWN:** Actual policies and evidence of use.

### K-009 — Durable audit lineage

- **Type:** Audit / memory framework
- **Description:** Preserve traceable records connecting input, source, specification, evaluation, authorization, action, and outcome.
- **Evidence:** Append-only audit and evidence linkage are repeated.
- **Source:** `C2_CORE_PRINCIPLES.md` 9; `APEX_CORE_WISDOM.md` 22–23; `C2_COGNITIVE_GRAPH.md` B7.
- **Related Atoms:** K-003, K-002, K-010, K-013, K-014
- **FACT:** Durable audit and traceability are named principles.
- **INFERENCE:** Link records across the whole decision lifecycle.
- **UNKNOWN:** Retention, access, and tamper-detection details.

### K-010 — Incident / risk / modeled-condition distinction

- **Type:** Failure knowledge / epistemic control
- **Description:** Do not report a forecast risk or modeled error path as a confirmed incident.
- **Evidence:** Failure and cognitive materials explicitly preserve this distinction and note no confirmed historical incidents in the source corpus.
- **Source:** `C2_FAILURE_PATTERNS.md` evidence limits and summary; `C2_CORE_PRINCIPLES.md` 14; `C2_META_BRAIN.md` 31–33.
- **Related Atoms:** K-001, K-009, K-011, K-014
- **FACT:** Source documents state no historical incident was confirmed in their bounded corpus.
- **INFERENCE:** Use separate labels and evidence fields for risks and incidents.
- **UNKNOWN:** Events outside the authorized sources.

### K-011 — Missing evidence means hold/UNKNOWN

- **Type:** Decision rule
- **Description:** Missing input or check is not a pass, a negative quality score, or a confirmed cause.
- **Evidence:** Multiple principles and failure patterns discuss missing evidence and null results.
- **Source:** `C2_CORE_PRINCIPLES.md` 12; `C2_DECISION_GRAPH.md` Q2; `C2_FAILURE_PATTERNS.md` patterns 2–3.
- **Related Atoms:** K-001, K-004, K-006, K-007, K-010
- **FACT:** The sources explicitly warn against treating absence as a result.
- **INFERENCE:** Use hold until missing evidence is supplied or an authorized exception is recorded.
- **UNKNOWN:** Exception conditions.

### K-012 — Progressive evidence review

- **Type:** Research / review framework
- **Description:** Move from broad screening to risk analysis to claim-level evidence checking.
- **Evidence:** A three-depth review model and risk-scaled investigation are named.
- **Source:** `C2_CORE_PRINCIPLES.md` 13; `APEX_CORE_WISDOM.md` 31; `C2_COGNITIVE_ARCHITECTURE.md` learning/evidence pipeline.
- **Related Atoms:** K-004, K-005, K-010, K-014
- **FACT:** Progressive analysis culminating in cited verification is documented.
- **INFERENCE:** Increase depth with impact and uncertainty.
- **UNKNOWN:** Triage thresholds.

### K-013 — Preserve invariants; replace context-bound logic

- **Type:** Migration strategy
- **Description:** Identify reusable controls separately from context-specific assumptions, then replace only what no longer fits.
- **Evidence:** Preserve/replace strategy is repeated in principles and decision reconstruction.
- **Source:** `C2_CORE_PRINCIPLES.md` 2; `C2_DECISION_GRAPH.md` T1/S1; `APEX_CORE_WISDOM.md` 8–9, 40.
- **Related Atoms:** K-008, K-009, K-015
- **FACT:** This is the documented strategic pattern.
- **INFERENCE:** Use adapters and compatibility review where dependencies remain.
- **UNKNOWN:** Complete invariant inventory.

### K-014 — Verified learning update

- **Type:** Learning framework
- **Description:** Convert outcomes into transferable knowledge only after comparing intended and observed results and verifying explanations.
- **Evidence:** Wisdom principles require verified root cause and caution against unsupported lessons.
- **Source:** `APEX_CORE_WISDOM.md` 21, 29, 49–50; `C2_COGNITIVE_GRAPH.md` B8.
- **Related Atoms:** K-001, K-009, K-010, K-012
- **FACT:** Evidence-based postmortem and verified learning are stated.
- **INFERENCE:** Version and review knowledge updates before changing policies.
- **UNKNOWN:** Automatic adaptation and learning effectiveness.

### K-015 — Meta-brain functions are not proven autonomous brains

- **Type:** Inventory / architecture status
- **Description:** Evaluation, audit, and orchestration are documented as functions; separate self-governing brains performing them are unconfirmed.
- **Evidence:** Cognitive Architecture and Meta Brain explicitly distinguish capability functions from autonomous agents.
- **Source:** `C2_COGNITIVE_ARCHITECTURE.md` 7–25, 29–43; `C2_META_BRAIN.md` 5–9, 15–16, 31–33, 48–59.
- **Related Atoms:** K-003, K-004, K-009, K-013
- **FACT:** The source set does not prove a fixed count or autonomous meta-brain.
- **INFERENCE:** Store capabilities as function nodes until implementation evidence exists.
- **UNKNOWN:** Actual topology and agent count.

## Relationships

| From | Relationship | To | Status |
|---|---|---|---|
| K-001 | classifies | K-002–K-015 | INFERENCE |
| K-004 | gates | K-006 | INFERENCE |
| K-005 | defines criteria for | K-006 | INFERENCE |
| K-007 | informs | K-006 | INFERENCE |
| K-006 | authorizes transition toward | K-002 / K-008 | INFERENCE |
| K-002 | precedes | consequential action | FACT in source model |
| K-009 | records | K-002–K-008 outcomes | INFERENCE |
| K-010 | constrains interpretation of | K-009 | INFERENCE |
| K-011 | routes insufficient evidence to | hold / UNKNOWN | FACT in source decision model |
| K-012 | deepens verification of | K-004 / K-010 | INFERENCE |
| K-013 | informs migration of | K-008 / K-009 | INFERENCE |
| K-014 | consumes verified records from | K-009 / K-010 | INFERENCE |
| K-015 | constrains claims about | cognitive topology | FACT in source set |

## UNKNOWN

No destination graph schema, stable external identifiers, confidence scale, or canonical relation vocabulary is specified by the authorized sources.
