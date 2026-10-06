# Framework — Failure Library / Risk–Incident Separation

- **ID:** FW-05
- **Purpose:** Prevent forecast risks from being recorded as actual incidents.
- **Structure:** Classify confirmed incident, modeled condition, forecast risk, or UNKNOWN; assign root cause only after verification.
- **Evidence:** `FRAMEWORK_LIBRARY.md`, F-05; `KNOWLEDGE_GRAPH_NODES.md`, K-010.
- **Related Seeds:** KS-005, KS-008
- **Status:** Distinction direct; full incident lifecycle is a candidate

**FACT:** The source materials warn against treating inferred patterns as confirmed incidents.  
**INFERENCE:** Keep separate evidence records and statuses.  
**UNKNOWN:** Historical events outside the bounded source set.
