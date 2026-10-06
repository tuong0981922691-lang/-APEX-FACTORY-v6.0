# KNOWLEDGE_DIRECTORY_STRUCTURE

## Logical directory tree

This is the canonical proposed layout for a future knowledge repository. The current bootstrap uses Markdown indexes and categorized objects; it does not assert that separate physical directories or a storage engine have already been provisioned.

```text
knowledge-base/
├── 00_QUY_UOC/
│   ├── Evidence_Status_Convention.md
│   └── Object_Schema.md
├── 01_INVENTORY/
│   ├── Cognitive_Capability_Inventory.md
│   └── Evidence_Status_Inventory.md
├── 02_KNOWLEDGE/
│   ├── KS-001.md ... KS-009.md
│   ├── packs/
│   └── reusable-assets/
├── 03_SOP/
│   └── candidates/
├── 04_PROMPT_LIBRARY/
│   └── candidates/
├── 05_KNOWLEDGE_GRAPH/
│   ├── MASTER_KNOWLEDGE_GRAPH_v1.md
│   └── KNOWLEDGE_OBJECT_INDEX.md
├── 06_STRATEGY/
│   └── Governance_and_Migration_Principles.md
├── 07_RESEARCH_ROADMAP/
│   └── RESEARCH_BACKLOG.md
└── 08_ACTION_PLAN/
    └── ACTION_BACKLOG.md
```

## Category mapping

| Directory | Contents | Current bootstrap representation |
|---|---|---|
| `00_QUY_UOC` | Metadata definitions, FACT/INFERENCE/UNKNOWN and confidence conventions | Conventions in this document and `KNOWLEDGE_OBJECT_INDEX.md` |
| `01_INVENTORY` | Claims about known knowledge objects/capabilities and evidence status | `KNOWLEDGE_OBJECT_INDEX.md`; capability status from the five inputs |
| `02_KNOWLEDGE` | Canonical knowledge objects, packs, reusable assets | `KNOWLEDGE_SEEDS.md`, `KNOWLEDGE_PACKS.md`, `REUSABLE_ASSETS.md` |
| `03_SOP` | Candidate and later approved procedures | `SOP_CANDIDATES.md`; not approved |
| `04_PROMPT_LIBRARY` | Candidate prompt templates | `PROMPT_CANDIDATES.md`; not validated as defaults |
| `05_KNOWLEDGE_GRAPH` | Nodes, typed relationships, graph versions | `KNOWLEDGE_GRAPH_NODES.md`, `MASTER_KNOWLEDGE_GRAPH.md` |
| `06_STRATEGY` | Transferable strategy principles and migration rules | `REUSABLE_ASSETS.md`, `KNOWLEDGE_ROADMAP.md` |
| `07_RESEARCH_ROADMAP` | UNKNOWNs, missing evidence, future domain coverage | `RESEARCH_BACKLOG.md` |
| `08_ACTION_PLAN` | Curation/import work in NOW/NEXT/LATER states | `ACTION_BACKLOG.md` |

## Object-state conventions

### FACT

- The requested categories and knowledge-object structure are defined by the bootstrap request.
- Source assets distinguish facts, inferences, unknowns, candidate SOPs/prompts, and conceptual graph relationships.

### INFERENCE

- Maintain one canonical object per stable ID; categories and packs should reference it rather than fork its content.
- Store source provenance, confidence rationale, status, and relationships with every object.
- A candidate should move to approved/active only through a documented human review.
- Keep the logical tree independent of any particular database or repository product.

### UNKNOWN

- Whether categories become physical directories, database namespaces, tags, or a combination.
- Required metadata fields, version format, identity service, permissions, archive policy, and approval owners.
- Whether source text must be retained in full or only provenance/citations.

## Migration guardrails

- Do not upgrade an inference into FACT during formatting or import.
- Do not remove an UNKNOWN label because the destination schema lacks a field; resolve the schema gap or retain the label in content.
- Do not activate candidate SOPs/prompts by moving or renaming files alone.
- Tag context-bound material `DOMAIN_SPECIFIC` and quarantine until an approved mapping is documented.
- Preserve node IDs and source links when organizing or splitting files.
