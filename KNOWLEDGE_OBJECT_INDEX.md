# KNOWLEDGE_OBJECT_INDEX

## Object schema

Each initial object is based on a seed and has:

- **ID**
- **Title**
- **Description**
- **Evidence**
- **Related Nodes**

**FACT:** The source seeds also provide a confidence label; this index retains it as auxiliary metadata.  
**INFERENCE:** Confidence reflects source support, not probability or operational effectiveness.  
**UNKNOWN:** Whether the destination object schema accepts confidence, status, or provenance as separate fields.

## Canonical knowledge objects

Canonical individual files are stored under `02_KNOWLEDGE/`; the index below is for navigation and status, not a second copy of object records.

### KO-001 (seed KS-001) — Keep fact, inference, and unknown distinct

- **ID:** KO-001 / KS-001
- **Title:** Keep fact, inference, and unknown distinct
- **Description:** Record evidence, interpretation, and missing information separately; do not promote interpretation or absence into a fact.
- **Evidence:** Source set repeatedly prescribes the three-way distinction.
- **Related Nodes:** K-001, K-006, K-010, K-011, K-014
- **Confidence:** High
- **Status:** Candidate knowledge object
- **FACT:** This convention is explicit and repeated in seed inputs.
- **INFERENCE:** Use as core metadata for all knowledge objects.
- **UNKNOWN:** Additional confidence/evidence grades required by the receiving system.

### KO-002 (seed KS-002) — Require accountable human authorization

- **ID:** KO-002 / KS-002
- **Title:** Require accountable human authorization
- **Description:** Separate evidence and evaluation from authorization; require an authorized person before consequential action.
- **Evidence:** Approval gate is stated in the framework and graph inputs.
- **Related Nodes:** K-002, K-003, K-006, K-008
- **Confidence:** High
- **Status:** Candidate knowledge object
- **FACT:** Human approval is represented as a precondition for consequential action.
- **INFERENCE:** Calibrate approval rigor to impact and reversibility.
- **UNKNOWN:** Authority hierarchy and exceptions.

### KO-003 (seed KS-003) — Validate claims before relying on them

- **ID:** KO-003 / KS-003
- **Title:** Validate claims before relying on them
- **Description:** State a claim and criteria, inspect provenance, run suitable checks, and compare to observed evidence before reliance.
- **Evidence:** Evidence verification framework and procedure candidate.
- **Related Nodes:** K-001, K-004, K-005, K-006, K-011
- **Confidence:** High
- **Status:** Candidate knowledge object
- **FACT:** Provenance, validation, independent checks, and artifact comparison are documented.
- **INFERENCE:** Missing checks should lead to hold, not silent acceptance.
- **UNKNOWN:** Complete criteria and thresholds.

### KO-004 (seed KS-004) — Maintain a durable evidence trail

- **ID:** KO-004 / KS-004
- **Title:** Maintain a durable evidence trail
- **Description:** Link input, specification, evaluation, authorization, action, result, and verified learning so a decision can be reconstructed.
- **Evidence:** Audit lineage framework and knowledge graph node.
- **Related Nodes:** K-002, K-003, K-009, K-010, K-014
- **Confidence:** Medium
- **Status:** Candidate knowledge object
- **FACT:** Append-only audit and traceability are documented.
- **INFERENCE:** Link the full decision lifecycle.
- **UNKNOWN:** Retention, access, integrity, completeness.

### KO-005 (seed KS-005) — Do not turn forecast into history

- **ID:** KO-005 / KS-005
- **Title:** Do not turn forecast into history
- **Description:** Distinguish confirmed incident, modeled error condition, forecast risk, and unknown; assign root cause only with evidence.
- **Evidence:** Failure classification framework and candidate failure-analysis procedure.
- **Related Nodes:** K-001, K-009, K-010, K-011, K-014
- **Confidence:** High
- **Status:** Candidate knowledge object
- **FACT:** The source materials warn against representing modeled risks as incidents.
- **INFERENCE:** Maintain separate evidence records for these categories.
- **UNKNOWN:** Events outside the source set and destination incident lifecycle.

### KO-006 (seed KS-006) — Represent functions without assuming agent count

- **ID:** KO-006 / KS-006
- **Title:** Represent functions without assuming agent count
- **Description:** Represent intake, framing, proposal, evaluation, decision, action, audit, and learning as linked capabilities without inferring autonomous agents.
- **Evidence:** Cognitive pipeline framework and capability-vs-agent node.
- **Related Nodes:** K-003, K-004, K-009, K-014, K-015
- **Confidence:** Medium
- **Status:** Candidate knowledge object
- **FACT:** Source materials do not establish a fixed autonomous-agent count.
- **INFERENCE:** Store capability nodes until component evidence exists.
- **UNKNOWN:** Actual topology and runtime autonomy.

### KO-007 (seed KS-007) — Stage change and preserve recovery

- **ID:** KO-007 / KS-007
- **Title:** Stage change and preserve recovery
- **Description:** Bound scope, define evidence/exit criteria, validate before impact, and preserve a recovery path.
- **Evidence:** Staged change framework and decision/migration candidates.
- **Related Nodes:** K-002, K-006, K-008, K-013
- **Confidence:** Medium
- **Status:** Candidate knowledge object
- **FACT:** Staging and pre-impact checking are documented design principles.
- **INFERENCE:** Set stop, exit, and recovery criteria for each stage.
- **UNKNOWN:** Actual policies and operational limits.

### KO-008 (seed KS-008) — Use progressive evidence review

- **ID:** KO-008 / KS-008
- **Title:** Use progressive evidence review
- **Description:** Begin with a broad scan, identify risks, then verify specific high-impact or uncertain claims with citations.
- **Evidence:** Progressive review framework and candidate investigation prompt.
- **Related Nodes:** K-004, K-010, K-011, K-012
- **Confidence:** Medium
- **Status:** Candidate knowledge object
- **FACT:** Progressive-depth, cited analysis is documented.
- **INFERENCE:** Review depth should reflect impact and uncertainty.
- **UNKNOWN:** Triage thresholds.

### KO-009 (seed KS-009) — Keep acceptance states distinct

- **ID:** KO-009 / KS-009
- **Title:** Accept, revise, reject, or hold
- **Description:** Distinguish acceptance, repair/review, rejection, and insufficient-evidence hold; record rationale and permitted next step.
- **Evidence:** Acceptance state machine framework and decision procedure candidate.
- **Related Nodes:** K-001, K-004, K-005, K-006, K-011
- **Confidence:** Medium
- **Status:** Candidate knowledge object
- **FACT:** These outcome classes are documented.
- **INFERENCE:** Record rationale and next transition for each outcome.
- **UNKNOWN:** Transition rules, retry limits, override authority.

## Index integrity

**FACT:** Nine seed records are available in the authorized input.  
**INFERENCE:** KO-001…KO-009 provide knowledge-object aliases while retaining original KS IDs to preserve lineage.  
**UNKNOWN:** Whether the receiving system prefers a single ID namespace or separate object IDs.

## Canonical file map

| Object | File |
|---|---|
| KO-001 / KS-001 | `02_KNOWLEDGE/KS-001.md` |
| KO-002 / KS-002 | `02_KNOWLEDGE/KS-002.md` |
| KO-003 / KS-003 | `02_KNOWLEDGE/KS-003.md` |
| KO-004 / KS-004 | `02_KNOWLEDGE/KS-004.md` |
| KO-005 / KS-005 | `02_KNOWLEDGE/KS-005.md` |
| KO-006 / KS-006 | `02_KNOWLEDGE/KS-006.md` |
| KO-007 / KS-007 | `02_KNOWLEDGE/KS-007.md` |
| KO-008 / KS-008 | `02_KNOWLEDGE/KS-008.md` |
| KO-009 / KS-009 | `02_KNOWLEDGE/KS-009.md` |
