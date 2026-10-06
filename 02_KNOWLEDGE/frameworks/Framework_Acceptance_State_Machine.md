# Framework — Acceptance State Machine

- **ID:** FW-09
- **Purpose:** Keep decision outcomes distinct rather than collapsing them into a binary.
- **Structure:** Accept / revise / reject / hold-UNKNOWN, with reason and next permitted transition.
- **Evidence:** `FRAMEWORK_LIBRARY.md`, F-09; `KNOWLEDGE_GRAPH_NODES.md`, K-006.
- **Related Seeds:** KS-003, KS-009
- **Status:** Outcome categories direct; transition rules are a candidate

**FACT:** Sources name accept, revise/fix, reject, and hold/UNKNOWN.  
**INFERENCE:** Record a rationale and next step for every state.  
**UNKNOWN:** Retry limits and override conditions.
