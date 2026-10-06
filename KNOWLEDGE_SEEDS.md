# KNOWLEDGE_SEEDS

## Evidence and confidence convention

Seeds are distilled only from the five authorized source files: `FRAMEWORK_LIBRARY.md`, `SOP_CANDIDATES.md`, `PROMPT_CANDIDATES.md`, `KNOWLEDGE_GRAPH_NODES.md`, and `MIGRATION_PLAN.md`.

**Confidence** describes how strongly the seed is supported by those documents, not statistical probability and not proof of operational effectiveness:

- **High:** explicitly stated and reinforced by multiple source records.
- **Medium:** clearly supported as a framework, but a material part is an inference or candidate.
- **Low:** mainly a proposed generalization; requires review before adoption.

All seeds are expressed as domain-neutral knowledge for future knowledge ecosystems. Each seed separates FACT, INFERENCE, and UNKNOWN.

## KS-001 — Evidence status taxonomy

- **ID:** KS-001
- **Title:** Keep fact, inference, and unknown distinct
- **Description:** Record direct evidence separately from interpretation and missing information. Do not silently promote an inference or absence of evidence into a fact.
- **Evidence:** F-01 explicitly defines the separation; K-001 encodes it; migration guidance requires preserving evidence status.
- **Related Nodes:** K-001, K-006, K-010, K-011, K-014
- **Confidence:** High
- **FACT:** The source set repeatedly prescribes FACT / INFERENCE / UNKNOWN separation.
- **INFERENCE:** Use this taxonomy as the minimum epistemic metadata for every imported claim.
- **UNKNOWN:** Whether a target knowledge system needs additional confidence or evidence grades.

## KS-002 — Human approval before consequential action

- **ID:** KS-002
- **Title:** Require accountable human authorization
- **Description:** Separate evidence gathering and evaluation from authorization; do not take consequential action without approval by an authorized person.
- **Evidence:** F-02 and K-002 describe the gate; the decision procedure candidate gives the sequence.
- **Related Nodes:** K-002, K-003, K-006, K-008
- **Confidence:** High
- **FACT:** Human authorization is documented as a precondition for consequential action.
- **INFERENCE:** Scale approval rigor with potential impact and reversibility.
- **UNKNOWN:** The complete authority hierarchy, exception rules, and approval record format.

## KS-003 — Verify before trust

- **ID:** KS-003
- **Title:** Validate claims before relying on them
- **Description:** State the claim and criteria, inspect source lineage, run applicable contract and independent checks, and compare with observed evidence before relying on an output.
- **Evidence:** F-03, K-004, and the evidence-verification procedure candidate.
- **Related Nodes:** K-001, K-004, K-005, K-006, K-011
- **Confidence:** High
- **FACT:** Validation, provenance, independent checks, and artifact comparison are documented.
- **INFERENCE:** A missing check should lead to hold, not silent acceptance.
- **UNKNOWN:** Complete validation criteria, baselines, thresholds, and conflict resolution.

## KS-004 — Preserve decision lineage

- **ID:** KS-004
- **Title:** Maintain a durable evidence trail
- **Description:** Link the originating input, specification, evaluation, authorization, action, outcome, and any verified learning so that a decision can be reconstructed.
- **Evidence:** F-04, K-009, and the audit procedure candidate.
- **Related Nodes:** K-002, K-003, K-009, K-010, K-014
- **Confidence:** Medium
- **FACT:** Durable append-only audit and traceability are documented.
- **INFERENCE:** A useful audit record links the full lifecycle rather than only the final result.
- **UNKNOWN:** Retention, access control, integrity verification, and current completeness.

## KS-005 — Separate incidents from risks

- **ID:** KS-005
- **Title:** Do not turn forecast into history
- **Description:** Label a confirmed incident, modeled error condition, forecast risk, and unknown as separate knowledge states. Record a root cause only when evidence supports it.
- **Evidence:** F-05, K-010, and failure-analysis prompt/procedure candidates.
- **Related Nodes:** K-001, K-009, K-010, K-011, K-014
- **Confidence:** High
- **FACT:** The source set warns that modeled risks must not be represented as confirmed incidents.
- **INFERENCE:** Keep separate records and evidence status for each category.
- **UNKNOWN:** Events outside the supplied materials and the target incident lifecycle.

## KS-006 — Model cognition as a gated capability pipeline

- **ID:** KS-006
- **Title:** Represent functions without assuming agent count
- **Description:** Model intake, clarification, proposal, evaluation, decision, action, audit, and learning as linked capabilities; do not infer independent agents from function labels.
- **Evidence:** F-06 and K-015 distinguish pipeline functions from proven autonomous agents.
- **Related Nodes:** K-003, K-004, K-009, K-014, K-015
- **Confidence:** Medium
- **FACT:** The sources identify functions and gates but do not establish a fixed autonomous-agent count.
- **INFERENCE:** Use capability nodes until separate implementation evidence exists.
- **UNKNOWN:** Actual topology, component ownership, and runtime autonomy.

## KS-007 — Change in bounded, reversible stages

- **ID:** KS-007
- **Title:** Stage change and preserve recovery
- **Description:** Bound the initial scope, define evidence and exit criteria, validate before impact, and retain a recovery path before expanding.
- **Evidence:** F-07, K-008, and the decision/migration candidates.
- **Related Nodes:** K-002, K-006, K-008, K-013
- **Confidence:** Medium
- **FACT:** Staging, pre-impact checking, and gradual rollout are documented design principles.
- **INFERENCE:** Every stage should have a stop condition, exit evidence, and recovery plan.
- **UNKNOWN:** Whether these controls are operational and what stage limits apply.

## KS-008 — Increase review depth with risk

- **ID:** KS-008
- **Title:** Use progressive evidence review
- **Description:** Begin with a broad screen, identify risks, then verify specific high-impact or uncertain claims with citations.
- **Evidence:** F-08, K-012, and the investigation prompt candidate.
- **Related Nodes:** K-004, K-010, K-011, K-012
- **Confidence:** Medium
- **FACT:** Progressive-depth analysis ending in cited verification is documented.
- **INFERENCE:** Spend deeper review effort where consequences or uncertainty are greater.
- **UNKNOWN:** Risk thresholds and how review effort is allocated.

## KS-009 — Keep acceptance states distinct

- **ID:** KS-009
- **Title:** Accept, revise, reject, or hold
- **Description:** Represent acceptance, fix-and-review, rejection, and insufficient-evidence hold as separate outcomes, each with a reason and next permitted step.
- **Evidence:** F-09 and K-006; the decision procedure candidate.
- **Related Nodes:** K-001, K-004, K-005, K-006, K-011
- **Confidence:** Medium
- **FACT:** The outcome categories appear in the documented decision model.
- **INFERENCE:** A state transition should be recorded with rationale and conditions.
- **UNKNOWN:** Complete transition rules, retry limits, and override authority.

## Provenance

**FACT:** The source knowledge distinguishes explicit principles from proposed operational procedures.  
**INFERENCE:** These seeds are migration-ready knowledge records, not activated controls.  
**UNKNOWN:** Target storage format and adoption owner.
