# KNOWLEDGE_DIRECTORY_STRUCTURE

## Logical directory tree

This is the canonical logical layout materialized by this bootstrap using Markdown files and indexes. It does not claim that a database, permission system, or automated storage engine has been provisioned.

```text
knowledge-base/
├── 00_QUY_UOC/
│   ├── Evidence_Status_Convention.md
│   └── Object_Schema.md
├── 01_INVENTORY/
│   └── Capability_Inventory.md
├── 02_KNOWLEDGE/
│   ├── KS-001.md ... KS-009.md
│   └── frameworks/
│       └── Framework_*.md
│   └── README.md
├── 03_SOP/
│   └── README.md
├── 04_PROMPT_LIBRARY/
│   └── README.md
├── 05_KNOWLEDGE_GRAPH/
│   └── MASTER_KNOWLEDGE_GRAPH_v1.md
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
| `00_QUY_UOC` | Metadata definitions, FACT/INFERENCE/UNKNOWN and confidence conventions | `00_QUY_UOC/Evidence_Status_Convention.md`, `Object_Schema.md` |
| `01_INVENTORY` | Claims about known knowledge objects/capabilities and evidence status | `01_INVENTORY/Capability_Inventory.md`, `KNOWLEDGE_OBJECT_INDEX.md` |
| `02_KNOWLEDGE` | Canonical knowledge objects and framework records; packs/assets remain root-level canonical references | `02_KNOWLEDGE/KS-001.md`…`KS-009.md`, `02_KNOWLEDGE/frameworks/`, `KNOWLEDGE_PACKS.md`, `REUSABLE_ASSETS.md` |
| `03_SOP` | Candidate and later approved procedures | `03_SOP/README.md` links `SOP_CANDIDATES.md`; not approved |
| `04_PROMPT_LIBRARY` | Candidate prompt templates | `04_PROMPT_LIBRARY/README.md` links `PROMPT_CANDIDATES.md`; not validated as defaults |
| `05_KNOWLEDGE_GRAPH` | Nodes, typed relationships, graph versions | `05_KNOWLEDGE_GRAPH/MASTER_KNOWLEDGE_GRAPH_v1.md` |
| `06_STRATEGY` | Transferable strategy principles and migration rules | `06_STRATEGY/README.md` links reusable assets and roadmap |
| `07_RESEARCH_ROADMAP` | UNKNOWNs, missing evidence, future domain coverage | `07_RESEARCH_ROADMAP/README.md` links `RESEARCH_BACKLOG.md` |
| `08_ACTION_PLAN` | Curation/import work in NOW/NEXT/LATER states | `08_ACTION_PLAN/README.md` links `ACTION_BACKLOG.md` |

The six requested root-level bootstrap deliverables remain canonical indexes and navigation points. The category directories provide materialized seed objects, per-framework records, and category entry points without duplicating candidate procedure/prompt content.

## Object-state conventions

### FACT

- The requested categories and knowledge-object structure are defined by the bootstrap request.
- The category files contain seed objects and one file per framework; the root indexes link to them.
- Source assets distinguish facts, inferences, unknowns, candidate SOPs/prompts, and conceptual graph relationships.

### INFERENCE

- Maintain one canonical object per stable ID; categories and packs reference it rather than fork its content.
- Store source provenance, confidence rationale, status, and relationships with every object.
- A candidate should move to approved/active only through a documented human review.
- Keep the logical tree independent of any particular database or repository product.

### UNKNOWN

- Whether this Markdown directory layout will later map to database namespaces, tags, or another storage system.
- Required metadata fields, version format, identity service, permissions, archive policy, and approval owners.
- Whether source text must be retained in full or only provenance/citations.

## Migration guardrails

- Do not upgrade an inference into FACT during formatting or import.
- Do not remove an UNKNOWN label because the destination schema lacks a field; resolve the schema gap or retain the label in content.
- Do not activate candidate SOPs/prompts by moving or renaming files alone.
- Tag context-bound material `DOMAIN_SPECIFIC` and quarantine until an approved mapping is documented.
- Preserve node IDs and source links when organizing or splitting files.
