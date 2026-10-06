# FRAMEWORK_LIBRARY

## Scope and evidence rule

This library uses only the seven authorized source documents: `C2_CORE_PRINCIPLES.md`, `C2_DECISION_GRAPH.md`, `C2_FAILURE_PATTERNS.md`, `APEX_CORE_WISDOM.md`, `C2_COGNITIVE_ARCHITECTURE.md`, `C2_COGNITIVE_GRAPH.md`, and `C2_META_BRAIN.md`.

**FACT:** A framework below is explicitly documented as such or is a named, repeated decision/learning structure in those sources.  
**INFERENCE:** “Candidate” frameworks are normalized structures that can be migrated to a new knowledge system.  
**UNKNOWN:** The sources do not establish implementation, completeness, or universal effectiveness.

## Knowledge classification map

The requested knowledge taxonomy is represented here and cross-linked to the other deliverables. It is a classification of the supplied knowledge, not a claim that every category already exists as an operational artifact.

| Category | What belongs here | Migration destination |
|---|---|---|
| `01_INVENTORY` | Cognitive capabilities, evidence status, explicit/indirect/hypothetical distinctions | `KNOWLEDGE_GRAPH_NODES.md`, `MIGRATION_PLAN.md` |
| `02_KNOWLEDGE` | Principles, verified facts, inferences, failure lessons, unknowns | This library; knowledge atoms in `KNOWLEDGE_GRAPH_NODES.md` |
| `03_SOP` | Candidate decision, verification, audit, learning procedures | `SOP_CANDIDATES.md`; candidates require review before adoption |
| `04_PROMPT_LIBRARY` | Reusable investigation, audit, reverse-analysis, extraction prompt patterns | `PROMPT_CANDIDATES.md`; derived templates, not source quotations |
| `05_KNOWLEDGE_GRAPH` | Atoms, types, relationships, evidence lineage | `KNOWLEDGE_GRAPH_NODES.md` |
| `06_STRATEGY` | Human authority, preserve invariants, staged and risk-aware change | `MIGRATION_PLAN.md` and principles atoms |
| `07_RESEARCH_ROADMAP` | Gaps whose resolution could change decisions or brain claims | `MIGRATION_PLAN.md` |
| `08_ACTION_PLAN` | Intake/review/hold actions for moving knowledge | `MIGRATION_PLAN.md`; not an implementation directive |

**FACT:** The source documents distinguish documented functions from standalone-brain claims and explicitly preserve UNKNOWN.  
**INFERENCE:** This taxonomy keeps knowledge, operational candidates, prompts, graph structure, strategy, research gaps, and migration actions from being conflated.  
**UNKNOWN:** Whether the target repository has a different canonical taxonomy or import schema.

## Frameworks

### F-01 — FACT / INFERENCE / UNKNOWN

- **Purpose:** Preserve the boundary between direct evidence, interpretation, and missing evidence.
- **Structure:** For each claim, record FACT, INFERENCE, and UNKNOWN separately; do not promote an inference or absence of data into a fact.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, principles 12 and 14; `APEX_CORE_WISDOM.md`, scope and principles 21, 24–25, 50; `C2_COGNITIVE_ARCHITECTURE.md`, scope.
- **Status:** Directly repeated framework.
- **FACT:** The seven sources repeatedly require explicit uncertainty and separation of evidence from inference.
- **INFERENCE:** Apply this as the base schema for every migrated atom and decision.
- **UNKNOWN:** Whether confidence scores or formal evidence grades exist.

### F-02 — Human Approval Gate

- **Purpose:** Keep authority for consequential action with an authorized human.
- **Structure:** Evidence and proposal → independent evaluation → explicit authorization → action; otherwise hold/reject.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, principles 1 and 4; `C2_DECISION_GRAPH.md`, T3 and acceptance/rejection gates; `APEX_CORE_WISDOM.md`, principles 1–2, 17, 19, 38.
- **Status:** Directly repeated principle and decision framework.
- **FACT:** Human approval and authorization are documented as preconditions for consequential actions.
- **INFERENCE:** Approval thresholds should scale with impact and reversibility.
- **UNKNOWN:** Complete authority model and exception policy.

### F-03 — Evidence Before Trust

- **Purpose:** Validate a claim or output before allowing it to influence a consequential decision.
- **Structure:** Define the claim and acceptance criteria → inspect provenance → check contract and independent evidence → accept, revise, reject, or hold.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, principles 3, 6–8; `C2_DECISION_GRAPH.md`, C2, T2, Q1–Q3; `C2_COGNITIVE_ARCHITECTURE.md`, pipeline.
- **Status:** Directly repeated verification framework.
- **FACT:** The source set describes contracts, critics, probes, and artifact comparison as validation mechanisms.
- **INFERENCE:** A missing check must not silently count as a pass.
- **UNKNOWN:** Complete criteria, baselines, thresholds, and conflict-resolution procedure.

### F-04 — Audit First / Evidence Lineage

- **Purpose:** Make decisions reconstructable from source through outcome.
- **Structure:** Preserve source/provenance, specification version, evaluation, authority, action, result, and any postmortem as linked records.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, principle 9; `APEX_CORE_WISDOM.md`, principles 22–23; `C2_COGNITIVE_GRAPH.md`, B7.
- **Status:** Audit principle directly documented; the full linked record is a normalized candidate.
- **FACT:** Append-only audit and traceability are repeated.
- **INFERENCE:** A decision record should link each stage, not merely record the final outcome.
- **UNKNOWN:** Retention, access control, integrity checks, and audit completeness.

### F-05 — Failure Library / Risk–Incident Separation

- **Purpose:** Prevent speculative risks from being recorded as actual failures.
- **Structure:** Classify item as incident with evidence, modeled failure condition, forecast risk, or UNKNOWN; record root cause only after verification.
- **Evidence:** `C2_FAILURE_PATTERNS.md`, evidence limits and summary; `APEX_CORE_WISDOM.md`, principles 21, 25, 45, 49.
- **Status:** Directly documented distinction; incident lifecycle details are candidate additions.
- **FACT:** The source set says no historical incident was confirmed and warns not to present inferred patterns as events.
- **INFERENCE:** Maintain separate records and confidence for incidents, risks, and test conditions.
- **UNKNOWN:** Historical failures outside the seven documents.

### F-06 — Cognitive Pipeline / Brain Architecture

- **Purpose:** Model how evidence moves through cognitive functions without assuming a fixed number of agents.
- **Structure:** Intake → clarification/framing → proposal → evaluation → human decision/authorization → action → audit → verified learning.
- **Evidence:** `C2_COGNITIVE_ARCHITECTURE.md`, pipeline and brain classification; `C2_COGNITIVE_GRAPH.md`, graph and B1–B8.
- **Status:** Functional pipeline is an explicit reconstruction; separate autonomous brains are unconfirmed.
- **FACT:** The sources identify functions and gates, not a proven count of autonomous brains.
- **INFERENCE:** Represent capabilities as graph nodes and label each explicit, indirect, or hypothetical.
- **UNKNOWN:** Actual topology, standalone agents, and adaptive learning.

### F-07 — Reversible, Staged Change

- **Purpose:** Bound the impact and cost of changes while preserving a path to recovery.
- **Structure:** Scope a small stage → define evidence and exit criteria → test → authorize → release gradually → verify/rollback.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, principle 11; `C2_DECISION_GRAPH.md`, S3; `APEX_CORE_WISDOM.md`, principles 15, 17–18, 39, 41.
- **Status:** Staging and testing are documented; the complete sequence is an inference.
- **FACT:** Phases, sandboxing, and gradual rollout are referenced as design/mitigation.
- **INFERENCE:** Each stage should have explicit stop, rollback, and exit criteria.
- **UNKNOWN:** Actual rollout policies and evidence of use.

### F-08 — Progressive Evidence Review

- **Purpose:** Allocate review effort according to risk and uncertainty.
- **Structure:** Broad scan → identify risks → test a specific hypothesis with citations.
- **Evidence:** `C2_CORE_PRINCIPLES.md`, principle 13; `APEX_CORE_WISDOM.md`, principles 31 and 48; `C2_COGNITIVE_ARCHITECTURE.md`, learning/evidence pipeline.
- **Status:** Three-depth analysis is documented; risk-based allocation is an inference.
- **FACT:** The sources describe progressive analysis culminating in evidence-backed verification.
- **INFERENCE:** Use deeper review for high-impact or weakly evidenced decisions.
- **UNKNOWN:** Triage thresholds and review effort allocation.

### F-09 — Acceptance State Machine

- **Purpose:** Avoid collapsing all outcomes into a binary yes/no.
- **Structure:** Accept / revise / reject / hold-UNKNOWN, with a defined reason and next permitted transition.
- **Evidence:** `C2_DECISION_GRAPH.md`, Q1 and acceptance/rejection gates; `C2_COGNITIVE_GRAPH.md`, B4–B5.
- **Status:** Outcome categories are documented; transition rules are a candidate normalization.
- **FACT:** Sources name accept, fix/revise, reject, and hold/UNKNOWN.
- **INFERENCE:** Record a reason and next step for every outcome.
- **UNKNOWN:** Full transition graph, retry limits, and override conditions.

## Migration cautions

**FACT:** Several named frameworks are recommendations/design concepts and are not evidence that a target system implements them.  
**INFERENCE:** Import them as versioned knowledge records with evidence status, not as active policies or automated controls.  
**UNKNOWN:** Target-system schema and owner approval for adopting any framework.
