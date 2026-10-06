# SOP_CANDIDATES

## Status and boundaries

This document contains **candidate procedures distilled from the seven authorized knowledge documents**. It does not claim they are existing SOPs, does not create an operational mandate, and requires review by the future knowledge-system owner before adoption.

**FACT:** The sources describe decision gates, evidence verification, append-only audit, and evidence-based learning.  
**INFERENCE:** These can be arranged into repeatable procedure candidates.  
**UNKNOWN:** Owners, systems, approvals, timing, exception rules, and target-specific controls.

## SOP-C01 — Decision with explicit uncertainty

1. **Intake:** Record the decision question, request, source, scope, and affected parties.
2. **Frame:** Identify required facts, assumptions, missing fields, and acceptance criteria.
3. **Classify:** Label statements FACT, INFERENCE, or UNKNOWN; cite evidence for FACT.
4. **Propose:** Prepare one or more bounded options and state trade-offs.
5. **Evaluate:** Check contract, evidence, risk, and declared independent criteria.
6. **Select state:** Accept, revise, reject, or hold as UNKNOWN/insufficient evidence.
7. **Authorize:** Obtain explicit approval from the authorized person before consequential action.
8. **Record:** Link the decision, rationale, evidence, authority, and next step in the audit trail.

- **FACT:** Decision sources describe these gates and outcome types (`C2_DECISION_GRAPH.md`, C1/C2/T3/Q1 and gates).
- **INFERENCE:** This sequence is a consolidated candidate, not a verified universal procedure.
- **UNKNOWN:** Decision owner, sign-off format, and thresholds.

## SOP-C02 — Evidence verification

1. State the claim to be checked and what evidence would count for/against it.
2. Record provenance and version for each source.
3. Check required structure/contract and run applicable independent checks.
4. Compare the claim against the relevant artifact or observed result.
5. Record conflicts, limitations, missing inputs, and metric limitations.
6. Return verified, revise, reject, or UNKNOWN; never convert a missing check into pass.
7. Preserve the evidence and reviewer decision for audit.

- **FACT:** Contract checks, independent evaluation, artifact comparison, and UNKNOWN handling recur in the sources.
- **INFERENCE:** Explicit claim-level criteria improve reproducibility.
- **UNKNOWN:** Which evidence types qualify for each future knowledge domain.

## SOP-C03 — Audit and incident classification

1. Capture event time, actor/role, source, scope, and linked artifacts.
2. Record observed facts separately from hypotheses.
3. Classify as confirmed incident, modeled failure condition, forecast risk, or UNKNOWN.
4. Stop or hold consequential action when a material warning or missing gate is found.
5. Record the decision, approval, action, outcome, and any rollback.
6. Do not assign root cause until supported by evidence.
7. Preserve the record append-only; restrict sensitive details to appropriate audiences.

- **FACT:** Sources require durable audit and distinguish incidents from risks; the source corpus has no confirmed historical incident.
- **INFERENCE:** The steps form an audit candidate for future use.
- **UNKNOWN:** Severity, escalation, retention, privacy and closure policies.

## SOP-C04 — Learning from a verified outcome

1. Select a decision or event with sufficient evidence and a traceable record.
2. Compare intended result with observed result.
3. Identify discrepancy and competing explanations.
4. Test explanations against available evidence; leave unresolved cause UNKNOWN.
5. Separate observed fact, inference, and transferable lesson.
6. Propose a knowledge update with source, scope, confidence/evidence status, and related atoms.
7. Request review before changing policy or decision criteria.
8. Version the approved update and link it to the originating record.

- **FACT:** The sources say learning should follow verified evidence and not infer root cause.
- **INFERENCE:** Human review/versioning limits unverified changes to the knowledge base.
- **UNKNOWN:** Reviewer, approval workflow, and learning-effectiveness measure.

## SOP-C05 — Stop and resume after a warning

1. Pause the affected consequential path.
2. Preserve the warning and context as observed, without rewriting it as a root cause.
3. Mark the affected decision HOLD/UNKNOWN if required evidence or authorization is missing.
4. Investigate at a depth proportional to impact and uncertainty.
5. Resume only after a documented resolution, required checks, and authorization.
6. Record whether the warning was incident, expected condition, or false alarm, with evidence.

- **FACT:** Stop-and-record guidance and risk-scaled investigation are present.
- **INFERENCE:** The resume gate is a safe procedural completion of that guidance.
- **UNKNOWN:** Exact warning severity and resume authority.

## SOP-C06 — Knowledge migration review

1. Assign each imported item to one taxonomy class: inventory, knowledge, SOP candidate, prompt candidate, graph, strategy, research roadmap, or action plan.
2. Split compound statements into atomic claims.
3. Attach source, evidence status, and related atoms.
4. Preserve original wording only where needed for provenance; normalize domain-specific terms only when meaning remains clear.
5. Mark derived templates/procedures as INFERENCE, not as source FACT.
6. Route conflicts, unsupported claims, and sensitive/high-impact policies for owner review.
7. Keep unresolved items UNKNOWN or quarantine them rather than deleting evidence.

- **FACT:** The requested taxonomy and atom fields are part of this migration task; source documents require evidence separation.
- **INFERENCE:** This procedure is a proposed migration workflow.
- **UNKNOWN:** Target import tooling and canonical ownership.
