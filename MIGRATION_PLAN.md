# MIGRATION_PLAN

## Purpose and source boundary

Classify and prepare the seven authorized knowledge documents for a new knowledge base. This is a migration plan, not an implementation or an approved SOP.

## Classification

| Group | Import content | Handling |
|---|---|---|
| `01_INVENTORY` | Cognitive functions, evidence status, confirmed vs hypothetical brain claims | Import as architecture inventory; distinguish capability from agent |
| `02_KNOWLEDGE` | Principles, decision criteria, failure patterns, evidence-status rules, unknowns | Atomize and preserve source/FACT/INFERENCE/UNKNOWN |
| `03_SOP` | Decision, verification, audit, learning procedure candidates | Keep as candidate; require owner review before becoming active procedure |
| `04_PROMPT_LIBRARY` | Investigation, decision reconstruction, audit, reverse-analysis, extraction, failure, cognitive mapping, learning prompts | Import as draft templates; mark inferred and unvalidated |
| `05_KNOWLEDGE_GRAPH` | Knowledge atoms and their dependencies/relationships | Import nodes and typed relationships; preserve provenance |
| `06_STRATEGY` | Human authority, preserve invariants, staged/reversible change, evidence-first policy | Import as strategy principles, not domain-specific implementation |
| `07_RESEARCH_ROADMAP` | Unknowns that could alter brain-count, gate, threshold, learning, or authority conclusions | Queue for evidence gathering only if separately authorized |
| `08_ACTION_PLAN` | Review, atomization, deduplication, status labeling, and import checks | Use as migration work items; not operational SOP |

### FACT

The seven source files contain principles, decision structures, failure patterns, cognitive functions, meta-brain assessments, and explicit UNKNOWNs. They do not specify a target database or canonical import schema.

### INFERENCE

Classification is about the role of each claim in the destination knowledge base. The same source paragraph may yield several atoms assigned to different groups; preserve cross-links rather than force one classification per document.

### UNKNOWN

Whether the new repository expects directories rather than tags, and whether its taxonomy has additional rules.

## 1. What can be imported immediately?

**FACT**

- The explicit FACT / INFERENCE / UNKNOWN distinction.
- Repeated knowledge atoms for human approval gates, verification before trust, structured acceptance, durable audit, staged change, and missing-evidence handling.
- The documented decision outcomes: accept, revise, reject, hold/UNKNOWN.
- The distinction between confirmed incidents, modeled error conditions, and forecast risks.
- The finding that a fixed number of autonomous brains is not established by the sources.

**INFERENCE**

Import these as versioned knowledge records with their source document, evidence status, and related atoms. Preserve wording that communicates uncertainty; do not convert a candidate procedure or capability node into an active policy.

## 2. What requires review?

**FACT**

The sources label several procedures as candidates or inferred models and leave authority, criteria, implementation, weights, thresholds, and operating details unresolved.

**INFERENCE**

Review before activation:

- SOP candidates for decision, evidence verification, audit, learning, warnings, and migration.
- Prompt candidates, since they are newly normalized templates rather than source quotations.
- Inferred cognitive nodes and graph relationships.
- Any proposed gate, threshold, exception, rollback rule, or automatic learning behavior.
- Domain-neutral substitutions where normalization may have changed the original nuance.

Approval should come from the future knowledge owner; the authorized sources do not name that owner.

## 3. What lacks sufficient evidence?

**FACT**

- A fixed “seven brains” system or any definitive number of autonomous brains.
- Independent evaluator/auditor/coordinator brains and an autonomous meta-brain.
- Brain ownership, implementation topology, runtime behavior, and learning adaptation.
- Complete criteria, thresholds, score weights, baselines, exception/override rules.
- Incident frequency, root causes, failed experiments, abandoned approaches, and mitigation deployment status.
- The target repository’s graph schema, prompt standards, and operational SOP conventions.

**INFERENCE**

Keep these out of “verified knowledge.” Add to `07_RESEARCH_ROADMAP` as unanswered questions only if later investigation is authorized.

## 4. What should be discarded or quarantined?

**FACT**

The cognitive and wisdom documents instruct domain removal, and the evidence corpus warns against treating unsupported or domain-specific content as universal.

**INFERENCE**

- **Discard from the portable core:** domain nouns, domain taxonomies, product names, implementation labels, and examples whose meaning cannot be generalized without losing specificity.
- **Quarantine for review:** any atom whose purported universal principle depends on a domain-specific threshold, measure, heuristic, or assumption.
- **Do not discard:** provenance, source distinctions, UNKNOWN status, caveats, or evidence of mismatch; these protect against overstating certainty.
- **Do not import as fact:** hypothetical brain counts, forecast risks as incidents, inferred root causes, and proposed safeguards as deployed controls.

**UNKNOWN**

The authorized sources do not enumerate every domain-specific term or define a target repository’s quarantine/deletion policy.

## Suggested migration order

1. **Inventory:** Register each of the seven source documents and its allowed scope.
2. **Atomize:** Split compound statements; assign stable IDs and one primary claim per atom.
3. **Classify:** Assign each atom to one or more taxonomy groups and mark FACT / INFERENCE / UNKNOWN.
4. **Link:** Add evidence provenance and relationships; avoid unsupported causal edges.
5. **Review:** Prioritize inferred procedures, prompts, meta-brain claims, and anything high impact.
6. **Import:** Load only approved atoms; preserve rejected/unknown material as review records rather than silently dropping it.
7. **Reconcile:** Check that no candidate framework has been mislabeled as implemented policy and that every imported atom retains source lineage.

### FACT

Sources recommend evidence-linked knowledge, explicit uncertainty, and review before changing decision policy.

### INFERENCE

The sequence above is a safe migration order derived from those principles; it is not an existing workflow proven in operation.

### UNKNOWN

No import tooling, target schema, acceptance owner, or review service is identified by the authorized material.
