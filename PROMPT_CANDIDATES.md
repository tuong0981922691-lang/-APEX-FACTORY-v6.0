# PROMPT_CANDIDATES

## Status

These are **new, domain-neutral candidate templates** distilled from the seven authorized knowledge documents. They are not quotations of original prompts and have not been validated for a target system. Replace bracketed fields before use; preserve FACT / INFERENCE / UNKNOWN separation.

### P-01 — Evidence-bounded investigation

> Investigate only the supplied materials: [allowed source list]. Do not consult other files or sources. Answer the question: [claim/question]. For each finding, provide: FACT with exact source and evidence; INFERENCE with reasoning and a clear label; UNKNOWN for unsupported details. Distinguish direct evidence from absence of evidence. Do not infer intent, implementation, or historical events from a design statement alone.

- **FACT:** Source set repeatedly requires evidence citations, bounded scope, and uncertainty labels.
- **INFERENCE:** Template makes those requirements operational for an investigation.
- **UNKNOWN:** Citation conventions and acceptable evidence types in the destination system.

### P-02 — Decision reconstruction

> Reconstruct the decision [decision identifier/question] using only [allowed evidence]. Return:
> 1. Decision
> 2. Input and provenance
> 3. Stated criteria and gates
> 4. Reasoning explicitly supported by sources
> 5. Outcome or available alternatives
> 6. What would cause accept, revise, reject, or hold
> 7. FACT / INFERENCE / UNKNOWN in separate sections.
> Do not attribute motives or fill missing criteria.

- **FACT:** Decision Graph uses decision/input/reasoning/outcome and documents these outcome categories.
- **INFERENCE:** Explicit gates and provenance improve decision traceability.
- **UNKNOWN:** Whether the destination system has an official decision record format.

### P-03 — Audit review

> Audit [decision/action/artifact] against [authorized policy/evidence set]. Build a trace from input and source through specification, evaluation, human authorization, action, and observed outcome. For every missing link, mark UNKNOWN. Classify findings as confirmed incident, modeled failure condition, forecast risk, or no finding. Separate observation from root-cause hypothesis. Do not claim compliance from a plan or design description without evidence of operation.

- **FACT:** Audit lineage, incident/risk separation, and implementation-vs-plan caution recur in sources.
- **INFERENCE:** The trace format is a useful audit prompt.
- **UNKNOWN:** Target-specific audit requirements and access rights.

### P-04 — Reverse engineering from artifact to specification

> Given [artifact] and [original specification], infer only what the artifact demonstrates. Produce:
> - observed structure and behavior;
> - claims in the specification supported by the artifact;
> - missing, contradictory, or unverifiable requirements;
> - evidence references for each item;
> - FACT / INFERENCE / UNKNOWN separated.
> Do not treat absence in the artifact as proof of intent, and do not declare the specification satisfied from superficial similarity.

- **FACT:** The source knowledge includes reverse comparison between an intended specification and a reconstructed artifact.
- **INFERENCE:** Bidirectional comparison can expose gaps while avoiding overclaiming.
- **UNKNOWN:** Completeness of any future reverse-analysis method.

### P-05 — Knowledge extraction and atomization

> From only [source set], extract reusable knowledge and split compound claims into atoms. For each atom provide ID, title, description, evidence, source, related atoms, and FACT / INFERENCE / UNKNOWN. Remove domain-specific nouns only when a domain-neutral replacement preserves meaning; otherwise quarantine the item for review. Do not turn proposed frameworks into verified facts.

- **FACT:** The migration task requires atom fields and taxonomy; prior materials emphasize preserving evidence status.
- **INFERENCE:** This template reduces loss of provenance and domain assumptions during migration.
- **UNKNOWN:** Atom granularity and target vocabulary.

### P-06 — Failure archaeology

> Review only [failure evidence]. For each candidate pattern, report name, observed signals, confirmed cause or UNKNOWN, consequence (observed vs possible), prevention, and FACT / INFERENCE. Label every item as confirmed incident, modeled error path, forecast risk, or inference. Do not invent failed experiments, abandoned directions, frequency, or root cause.

- **FACT:** Failure Patterns explicitly warn that modeled risks are not confirmed incidents.
- **INFERENCE:** Labels prevent hypothetical failures from contaminating institutional memory.
- **UNKNOWN:** Target incident schema and required severity fields.

### P-07 — Cognitive capability mapping

> From [authorized knowledge sources], map cognitive functions without assuming a fixed agent count. For each candidate node provide function, input, output, dependencies, evidence, and status: directly evidenced function / indirect function / hypothesis / UNKNOWN. Separate the existence of a function from the existence of an autonomous brain implementing it. Describe evaluator, auditor, and coordinator roles independently.

- **FACT:** Cognitive sources explicitly prohibit forcing a fixed brain count and distinguish functions from autonomous agents.
- **INFERENCE:** This prompt is suitable for architecture reconstruction under sparse evidence.
- **UNKNOWN:** Evidence needed to promote a capability from function to verified autonomous component.

### P-08 — Learning review

> Review [verified outcome/postmortem]. Compare intended and observed results. List observations, alternative explanations, evidence for/against each explanation, unresolved UNKNOWNs, and candidate transferable lessons. Do not claim causal learning from correlation. Recommend a knowledge update only with provenance, scope, review status, and links to related atoms.

- **FACT:** Source wisdom requires learning from verified outcomes and not asserting unverified causes.
- **INFERENCE:** Explicit alternatives and review status reduce premature policy changes.
- **UNKNOWN:** How to measure whether a lesson improves future decisions.
