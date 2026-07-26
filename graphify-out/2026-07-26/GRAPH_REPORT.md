# Graph Report - AILearn  (2026-07-26)

## Corpus Check
- 214 files · ~215,529 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 34 nodes · 30 edges · 8 communities (5 shown, 3 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ffc6dc7b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Recent Work Completed
- Active Context — WebAI Platform
- Open Questions / Decisions Pending
- Immediate Next Steps (If User Requests)
- Current Session (2026-07-18)
- AGENTS.md
- rules/graphify.md
- workflows/graphify.md

## God Nodes (most connected - your core abstractions)
1. `Active Context — WebAI Platform` - 10 edges
2. `Recent Work Completed` - 8 edges
3. `Open Questions / Decisions Pending` - 6 edges
4. `Immediate Next Steps (If User Requests)` - 4 edges
5. `Current Session (2026-07-18)` - 3 edges
6. `graphify` - 1 edges
7. `graphify` - 1 edges
8. `Workflow: graphify` - 1 edges
9. `What Was Done Today` - 1 edges
10. `Current State of the Codebase` - 1 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Communities (8 total, 3 thin omitted)

### Community 0 - "Recent Work Completed"
Cohesion: 0.25
Nodes (8): API Server Startup Bug Fixes ✅, Database Migrations ✅, Graphify Knowledge Graph Integration ✅, Hermes 3 Model Integration ✅, Phase 8.2: Save Extracted Data ✅, Phase 8.3: Table Extraction ✅, Phase 9.1: Add Delay ✅, Recent Work Completed

### Community 1 - "Active Context — WebAI Platform"
Cohesion: 0.29
Nodes (6): Active Context — WebAI Platform, Active Files (Most Recently Modified), Key Context for Next Session, Pagination Config Ranges (from `recorder.py` lines 943-959), Related Documents, Running Services Status

### Community 2 - "Open Questions / Decisions Pending"
Cohesion: 0.33
Nodes (6): 1. Conditional Branching (Future Enhancement), 2. Variable Storage for Conditions, 3. Explicit Page Validation, 4. LOCATOR_PRIORITY Inconsistency, 5. Shim Module Bug, Open Questions / Decisions Pending

### Community 3 - "Immediate Next Steps (If User Requests)"
Cohesion: 0.50
Nodes (4): Immediate Next Steps (If User Requests), Option A: Implement Conditional Branching, Option B: Fix Known Issues, Option C: Testing & Stabilization

### Community 4 - "Current Session (2026-07-18)"
Cohesion: 0.67
Nodes (3): Current Session (2026-07-18), Current State of the Codebase, What Was Done Today

## Knowledge Gaps
- **25 isolated node(s):** `graphify`, `graphify`, `Workflow: graphify`, `What Was Done Today`, `Current State of the Codebase` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Active Context — WebAI Platform` connect `Active Context — WebAI Platform` to `Recent Work Completed`, `Open Questions / Decisions Pending`, `Immediate Next Steps (If User Requests)`, `Current Session (2026-07-18)`?**
  _High betweenness centrality (0.566) - this node is a cross-community bridge._
- **Why does `Recent Work Completed` connect `Recent Work Completed` to `Active Context — WebAI Platform`?**
  _High betweenness centrality (0.305) - this node is a cross-community bridge._
- **Why does `Open Questions / Decisions Pending` connect `Open Questions / Decisions Pending` to `Active Context — WebAI Platform`?**
  _High betweenness centrality (0.227) - this node is a cross-community bridge._
- **What connects `graphify`, `graphify`, `Workflow: graphify` to the rest of the system?**
  _25 weakly-connected nodes found - possible documentation gaps or missing edges._