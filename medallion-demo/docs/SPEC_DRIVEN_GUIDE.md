# Spec-Driven Development Guide

## How This Project Uses OpenSpec

Every feature in this medallion pipeline is driven by formal specifications.
This ensures that AI coding agents implement exactly what was designed and
reviewed, not what they hallucinate.

## The Workflow

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│  1. SPEC   │───▶│  2. REVIEW │───▶│  3. BUILD  │───▶│ 4. ARCHIVE │
│  /opsx:new │    │  Human     │    │  /opsx:apply│    │ /opsx:archive│
│  /opsx:ff  │    │  approves  │    │  Agent codes│    │ Update specs │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
```

### Step 1: Create a Change

```bash
# Tell your AI agent what you want
/opsx:new add-customer-360-gold

# Fast-forward: agent generates proposal, design, tasks, spec deltas
/opsx:ff
```

This creates:
```
openspec/changes/add-customer-360-gold/
├── proposal.md          ← Why and what (business context)
├── design.md            ← How (technical approach)
├── tasks.md             ← Implementation plan with checkboxes
└── specs/
    └── gold-aggregation/
        └── spec.md      ← Requirement deltas (what changes)
```

### Step 2: Human Reviews the Spec

**This is the critical gate.** Before any code is written, a human reviews:

1. **proposal.md** — Is this the right thing to build?
2. **design.md** — Is the technical approach sound?
3. **spec deltas** — Are the requirement changes correct?

The agent does NOT write code until the spec is approved. This prevents:
- AI agents building the wrong thing at high speed
- Hallucinated requirements that nobody asked for
- Scope creep in automated implementations

### Step 3: Agent Implements Against Spec

```bash
# Agent reads the approved spec and implements
/opsx:apply
```

The agent:
1. Reads the spec requirements (REQ-GLD-002, etc.)
2. Implements each requirement with code
3. References spec IDs in docstrings
4. Writes tests that verify spec scenarios
5. Checks off tasks in `tasks.md`

### Step 4: Archive and Update Living Specs

```bash
# Merge spec deltas into the living specs
/opsx:archive
```

This updates `openspec/specs/gold-aggregation/spec.md` with the new
requirements, creating a permanent record.

## Living Specs in This Project

| Spec | Layer | Description |
|------|-------|-------------|
| `bronze-ingestion/spec.md` | Bronze | Ingestion requirements (REQ-BRZ-*) |
| `silver-transformation/spec.md` | Silver | Transform requirements (REQ-SLV-*) |
| `gold-aggregation/spec.md` | Gold | Aggregate requirements (REQ-GLD-*) |
| `data-quality/spec.md` | Cross-layer | Quality framework (REQ-DQ-*) |

## Example: How Customer 360 Was Built

```
1. Spec created:  openspec/specs/gold-aggregation/spec.md (REQ-GLD-002)
2. Change opened: openspec/changes/add-customer-360-gold/
3. Agent generated: proposal.md, design.md, tasks.md, spec deltas
4. Human reviewed: Approved RFM algorithm, LTV thresholds
5. Agent built:   src/gold/customer_360.py (references REQ-GLD-002)
6. Agent tested:  tests/unit/test_customer_360.py (verifies spec scenarios)
7. Agent added:   dbt/models/gold/gold_customer_360.sql
8. Archived:      Spec deltas merged into living spec
```

## Why Spec-Driven > Prompt-Driven

| Prompt-Driven | Spec-Driven |
|---------------|-------------|
| "Build a customer 360 table" | REQ-GLD-002 defines exact columns, tiers, segments |
| Context lost between sessions | Specs persist in git, survive agent restarts |
| No review gate before code | Human reviews spec before any code is written |
| Hard to test "did we build the right thing" | Tests verify spec scenarios directly |
| Agent hallucinations go unchecked | Spec deltas show exactly what changes |
```
