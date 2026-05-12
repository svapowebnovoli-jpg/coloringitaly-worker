# Map Revision Protocol Integration — Batch 2 Hardening

**Status:** Implementation directive for Map Branch  
**Date:** 2026-05-12  
**Applies to:** Map Strategy Agent, Map Structure Agent, Map Style Agent

---

## Overview

Maps need the same **revision_round capping** as the core V3 system (max 2 rounds, then `needs_human_review=true`). Currently:

- **Map Strategy Agent** — No revision loop defined
- **Map Structure Agent** — No revision loop defined  
- **Map Style Agent** — No revision loop defined
- **Map QA Agent** — Has pass/revise/reject but no round capping

This directive adds bounded revision to Strategy/Structure/Style and enforces the 2-round cap across the map pipeline.

---

## What Gets Revision Loop (and Why)

| Agent | Revises | Example | Max Rounds |
|-------|---------|---------|-----------|
| **Map Strategy Agent** | map_blueprint (product_goal, narrative_goal, primary_focus coherence) | "Geisha map should focus on tea culture + craft, not general tourism" → revise, resubmit | 2 |
| **Map Structure Agent** | map_structure (POI grouping, route logic, area organization) | "These 5 POI don't fit the narrative; redistribute them" → revise, resubmit | 2 |
| **Map Style Agent** | style_profile (palette, line treatment, reference appropriateness) | "Palette is too bright; tone down for editorial feel" → revise, resubmit | 2 |
| **Map QA Agent** | qa_report (reject low-confidence outputs) | "Labels overlap; geometry incorrect" → output sent back to Generation for re-render | N/A (QA doesn't revise; it blocks or escalates) |

---

## Implementation Rules

### Rule 1: Map Job Input — Add revision_round Field

**Current Map Job schema:**
```json
{
  "job_id": "string",
  "mode": "factory|manual_seed|collection_expansion|auto",
  "country": "string",
  ...
}
```

**Add this field:**
```json
{
  "job_id": "string",
  "revision_round": 1,
  "mode": "factory|manual_seed|collection_expansion|auto",
  ...
}
```

**Rules:**
- `revision_round` starts at 1
- Increments by 1 each time an agent outputs `revision_reason` (indicates a request to revise and resubmit)
- Defaults to 1 if not provided

---

### Rule 2: Each Map Agent Output — Add Revision Fields

For **Map Strategy Agent**, **Map Structure Agent**, **Map Style Agent** outputs:

```json
{
  "map_blueprint": { ... },
  "revision_round": 1,
  "revision_reason": null | "string",
  "applied_adjustments": [],
  "remaining_open_questions": [],
  "status": "ready" | "revise_requested"
}
```

**Fields:**

| Field | Type | Meaning |
|-------|------|---------|
| `revision_round` | number | Current round (1 or 2 for these agents) |
| `revision_reason` | string \| null | Why this output needs revision (if `status=revise_requested`), or null if ready |
| `applied_adjustments` | array | What changed from last round (round 2 only) |
| `remaining_open_questions` | array | What's still uncertain and why (flags for QA or human) |
| `status` | string | "ready" (handoff now) or "revise_requested" (send back for changes) |

---

### Rule 3: Escalation at Round 2 Revise

**If any agent outputs:**
```
revision_round: 2
status: revise_requested
```

**Then automatically add:**
```json
{
  "needs_human_review": true,
  "review_reasons": [
    "Map revision loop exhausted (round 2 revise); geography/composition requires human cartographer sign-off"
  ],
  "ready_but_flagged": true
}
```

**Meaning:** The output can continue to QA, but it's flagged as "human cartographer review required before final publication."

---

### Rule 4: Revision Governance

| Scenario | Handling |
|----------|----------|
| Round 1 revise requested | Agent returns revised output with `revision_round=2`. Automatically re-queued. |
| Round 2 revise requested | Agent outputs `needs_human_review=true` + `ready_but_flagged=true`. Handoff continues (not blocked), but flagged. |
| Round 2 still has `remaining_open_questions` | Human cartographer or curator reviews before publication (Batch 2 only). |

---

## Integration Checklist

### For Map Strategy Agent

- [ ] Accept `revision_round` from Map Job input
- [ ] Output `revision_round`, `revision_reason`, `applied_adjustments`, `remaining_open_questions`, `status`
- [ ] If strategy doesn't cohere after round 2 → set `needs_human_review=true`
- [ ] Example: "Narrative goal (geisha culture) conflicts with primary_focus list (mix of sacred + craft). Adjust focus or reframe narrative?"

### For Map Structure Agent

- [ ] Accept `revision_round` from Map Job input  
- [ ] Output `revision_round`, `revision_reason`, `applied_adjustments`, `remaining_open_questions`, `status`
- [ ] If POI/route assignment doesn't work after round 2 → set `needs_human_review=true`
- [ ] Example: "5 tea houses clustered too densely; label spacing will fail. Redistribute geographically?"

### For Map Style Agent

- [ ] Accept `revision_round` from Map Job input
- [ ] Output `revision_round`, `revision_reason`, `applied_adjustments`, `remaining_open_questions`, `status`
- [ ] If palette/line treatment doesn't match style_reference after round 2 → set `needs_human_review=true`
- [ ] Example: "Palette is too vibrant for editorial minimalism. Tone down or use different reference?"

### For Map Generation Agent

- [ ] Accept `revision_round` from upstream outputs
- [ ] **Does NOT have revision loop** — it produces render_prompt once
- [ ] If rejected by QA → escalate to appropriate upstream agent (Strategy/Structure/Style)
- [ ] Example: "POI placement failed. Structure Agent needs to redistribute areas."

### For Map QA Agent

- [ ] Accept `revision_round` from upstream
- [ ] Output `qa_status` (pass / revise / reject)
- [ ] If revise → send back to Map Generation Agent or appropriate upstream
- [ ] If reject → escalate with specific blocking issues

---

## Example: Kyoto Map Round 1 → Round 2 → Escalation

### Round 1: Map Strategy Agent

```json
{
  "map_blueprint": {
    "map_type": "illustrated_neighborhood_map",
    "product_goal": "Educational coloring + reference guide for Kyoto neighborhoods",
    "narrative_goal": "Show how Kyoto's geisha and craft districts are organized and connected",
    "primary_focus": ["Gion", "Arashiyama", "Higashiyama", "Imperial Palace", "Philosopher's Walk"],
    "detail_level": "medium"
  },
  "revision_round": 1,
  "revision_reason": null,
  "applied_adjustments": [],
  "remaining_open_questions": [],
  "status": "ready"
}
```

**QA/Curator feedback:** "Imperial Palace and Philosopher's Walk don't fit geisha + craft narrative. Too many areas for medium detail."

### Round 2: Map Strategy Agent (Revised)

```json
{
  "map_blueprint": {
    "map_type": "illustrated_neighborhood_map",
    "product_goal": "Educational coloring + reference guide for Kyoto geisha and craft districts",
    "narrative_goal": "Show how Kyoto's geisha and craft neighborhoods are organized; trade routes between them.",
    "primary_focus": ["Gion (geisha culture)", "Higashiyama (craft shops)", "Arashiyama (temples)"],
    "detail_level": "medium"
  },
  "revision_round": 2,
  "revision_reason": null,
  "applied_adjustments": [
    "Removed Imperial Palace and Philosopher's Walk (don't fit geisha+craft narrative)",
    "Reframed narrative to emphasize trade/movement between three core districts",
    "Reduced primary_focus from 5 to 3 areas (improves coherence for medium detail level)"
  ],
  "remaining_open_questions": [],
  "status": "ready"
}
```

**Structure Agent succeeds. Generation Agent succeeds. QA Agent:**

```json
{
  "qa_status": "revise",
  "blocking_issues": [
    "Tea house labels overlap in Gion district (spacing = 0.15in, minimum required = 0.2in)",
    "Philosopher's Walk dashed line still visible in background layer (should be removed)"
  ],
  "minor_issues": [
    "Legend scale bar could be larger for print readability"
  ],
  "human_review_required": false,
  "release_readiness": "ready_for_manual_review"
}
```

→ **Generation Agent is asked to fix label spacing + remove background artifact.**

---

## Batch 2 vs. Batch 3 Scoping

### Batch 2 (Implementable Now)

Maps with:
- **Low-medium complexity** (neighborhoods, scenic routes, market districts)
- **3–5 primary areas**
- **Simple POI logic** (well-established categories)
- **Clear narrative** (geisha + craft, market + food, walking circuits)

**Revision handling:** 2 rounds, escalate to human if round 2 revise. Human review is **editorial** (narrative coherence, bundle fit), not cartographic complexity.

**Examples:** Kyoto neighborhoods, Siena districts, Florence art route, Palermo market quarters.

### Batch 3 (Not Yet Publish-Safe)

Maps with:
- **High complexity** (multi-layer historical + cultural + topographic)
- **6+ primary areas** OR **dense POI sets** (50+ items)
- **Intricate route logic** (pilgrimage paths, trade routes, administrative boundaries)
- **Accuracy-critical content** (historical overlays, archaeological sensitivity)

**Revision handling:** Same 2-round cap, but escalation goes to **cartographer + historian + cultural expert**, not just editorial curator.

**Status:** Blocking on infrastructure (we don't have the expert agents yet for these reviews).

**Examples:** Provence historical maps, Japanese imperial routes, Alpine pilgrim circuits.

---

## Deployment Checklist

- [ ] Update Map Job schema to include `revision_round` field
- [ ] Update Map Strategy Agent output contract (add revision fields)
- [ ] Update Map Structure Agent output contract (add revision fields)
- [ ] Update Map Style Agent output contract (add revision fields)
- [ ] Wire revision feedback into n8n Map Factory workflow
- [ ] Document escalation path: Round 2 revise → editorial curator review queue
- [ ] Tag outputs with `batch: 2` (ready now) vs. `batch: 3` (deferred)
- [ ] Test: `kyoto_maps_001` (Batch 2, 3 neighborhoods) — should pass with 0 or 1 revision
- [ ] Test: `provence_maps_001` (Batch 3, complex historical) — should escalate at round 2

---

## Success Criteria

✅ **Batch 2 maps** can complete revision loop in max 2 rounds with editorial-level feedback  
✅ **Batch 3 maps** are clearly flagged `needs_human_review=true` by round 2  
✅ **No infinite revision loops** — system forces decision at round 2 (escalate or reject)  
✅ **Rehoming tracked** — unused POI are logged for future homes, not lost
