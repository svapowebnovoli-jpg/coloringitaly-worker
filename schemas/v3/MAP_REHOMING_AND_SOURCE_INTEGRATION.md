# Map Rehoming & Source Verification Integration — Batch 2 Hardening

**Status:** Implementation directive for Map Branch  
**Date:** 2026-05-12  
**Applies to:** Map Job Input, Map Structure Agent, Map QA Agent, rehoming_log.json

---

## Gap 4: Rehoming Integration

### Problem

Maps identify POI, areas, or routes that are:
- ✅ Brand-fit (editorially strong, Ink & Roads–aligned)
- ❌ Not used in current map (don't fit this specific narrative or geography)

**Today:** These items are lost.  
**Solution:** Log them for future homes.

---

### Fix: Add rehoming_suggestions to Map Outputs

#### In Map Structure Agent Output

```json
{
  "map_structure": {
    "primary_areas": ["Gion", "Higashiyama", "Arashiyama"],
    "poi_groups": [...]
  },
  "unused_candidates": [
    {
      "item": "Philosopher's Walk (scenic northern route)",
      "why_excluded": "Too long for neighborhood focus; doesn't connect primary three districts",
      "brand_fit": "high",
      "suggested_future_home": "Kyoto Walking Circuits (multi-day edition)",
      "notes": "Strong for route-focused map variant"
    },
    {
      "item": "Imperial Palace complex (Gosho)",
      "why_excluded": "Not central to geisha+craft narrative",
      "brand_fit": "high",
      "suggested_future_home": "Historical Kyoto: Imperial & Administrative Centers",
      "notes": "Better as centerpiece of different map"
    }
  ]
}
```

#### In Map QA Agent Output

```json
{
  "qa_report": {
    "qa_status": "pass",
    "blocking_issues": [],
    "minor_issues": []
  },
  "rehoming_suggestions": [
    {
      "item": "Teacup icon variant (gold outline version unused in final render)",
      "suggested_by_agent": "Map QA Agent",
      "suggested_future_home": "Premium Kyoto Map variant (luxury edition)",
      "why": "Generated but not needed for editorial version; high-quality asset worth preserving",
      "status": "pending"
    }
  ]
}
```

---

### Integration: rehoming_log.json

**Workflow:**

1. **Map Structure Agent** outputs `unused_candidates[]`
2. **Map QA Agent** outputs `rehoming_suggestions[]`
3. **Map Packaging Agent** collects both and writes to `rehoming_log.json`

**rehoming_log.json format:**

```json
{
  "log_date": "2026-05-12",
  "collection": "kyoto_maps_001",
  "entries": [
    {
      "item": "Philosopher's Walk (scenic northern route)",
      "suggested_by_agent": "Map Structure Agent",
      "suggested_future_home": "Kyoto Walking Circuits (multi-day edition)",
      "why": "Too long for neighborhood focus; strong for route-focused variant",
      "brand_fit": "high",
      "status": "pending",
      "contributors": ["Map Structure Agent"],
      "created": "2026-05-12T10:30:00Z",
      "last_updated": "2026-05-12T10:30:00Z"
    },
    {
      "item": "Imperial Palace complex (Gosho)",
      "suggested_by_agent": "Map Structure Agent",
      "suggested_future_home": "Historical Kyoto: Imperial & Administrative Centers",
      "why": "Important historically but not central to geisha+craft narrative",
      "brand_fit": "high",
      "status": "pending",
      "contributors": ["Map Structure Agent"],
      "created": "2026-05-12T10:30:00Z",
      "last_updated": "2026-05-12T10:30:00Z"
    },
    {
      "item": "Teacup icon variant (gold outline)",
      "suggested_by_agent": "Map QA Agent",
      "suggested_future_home": "Premium Kyoto Map variant (luxury edition)",
      "why": "Generated but unused in editorial version; high-quality asset for premium product",
      "brand_fit": "high",
      "status": "pending",
      "contributors": ["Map QA Agent"],
      "created": "2026-05-12T11:00:00Z",
      "last_updated": "2026-05-12T11:00:00Z"
    }
  ]
}
```

**Merge rule (G7):** If same item suggested 2+ times, append agents to `contributors` field:

```json
{
  "item": "Philosopher's Walk",
  "suggested_by_agent": "Map Structure Agent", 
  "contributors": ["Map Structure Agent", "Map Strategy Agent"],
  "status": "pending"
}
```

---

## Gap 5: Source Verification

### Problem

Maps need credible geographic/editorial basis. Without source tracking:
- Can't defend accuracy claims
- Risk of generic tourism stereotypes (G9 violation)
- Can't distinguish editorial interpretation from factual error

### Fix: Add source_refs to Map Job Input & Map Structure Output

#### Update Map Job Input Schema

```json
{
  "job_id": "kyoto_maps_001",
  "country": "Japan",
  "region": "Kyoto Prefecture",
  "product_goal": "Educational neighborhood map",
  "source_mode": "editorial_research",
  "source_refs": [
    {
      "title": "Geisha: The Secret History of a Vanishing Kyoto World",
      "author": "Lesley Downer",
      "type": "book",
      "confidence": "high",
      "relevance": "Geisha districts, tea culture, geographic accuracy"
    },
    {
      "title": "Arashiyama Bamboo Grove and Temple Circuit",
      "url": "https://example.com/...",
      "type": "travel_guide_editorial",
      "confidence": "medium",
      "relevance": "Walking routes, temple locations, district boundaries"
    },
    {
      "title": "Local craft shops in Higashiyama — OpenStreetMap community survey",
      "source": "osm_community",
      "confidence": "medium",
      "relevance": "Craft shop locations (for reference, not as data source)"
    }
  ],
  "source_mode_notes": "Sources are editorial reference only. Map is a narrative interpretation, not GIS-accurate cadastral data."
}
```

#### Update Map Structure Agent Output

```json
{
  "map_structure": {
    "primary_areas": ["Gion", "Higashiyama", "Arashiyama"]
  },
  "source_refs": [
    {
      "title": "Geisha: The Secret History of a Vanishing Kyoto World",
      "relevance": "Gion district boundaries and tea culture POI",
      "confidence": "high",
      "used_for": "primary_areas, tea_culture_poi"
    },
    {
      "title": "Arashiyama Bamboo Grove and Temple Circuit",
      "confidence": "medium",
      "used_for": "route_layers, secondary_areas",
      "notes": "Used for walking path validation, not as cartographic baseline"
    }
  ],
  "needs_verification_items": [
    {
      "item": "Craft shop density in Higashiyama",
      "why": "POI list from OpenStreetMap community; should be spot-checked with local source",
      "confidence": "medium"
    }
  ]
}
```

---

### Guidelines: What Counts as Source

| Type | Confidence | Use Case |
|------|-----------|----------|
| Published book (geisha history, regional guide) | High | District identity, cultural POI, narrative framing |
| Travel guide editorial (regional tourism site) | Medium | Route validation, area boundaries, general geography |
| OpenStreetMap / community-sourced data | Medium | Reference only (not cartographic authority) |
| Personal research / local expert interviews | High (if documented) | Insider perspective, cultural nuance, local naming |
| Snazzy Maps style reference | Low (visual only) | Visual family inspiration, NOT data source |

---

### CRITICAL: Snazzy Maps Not a Data Source

**Rule:** Snazzy Maps is **style reference only**, never geographic/data source.

```json
{
  "style_profile": {
    "style_reference_notes": [
      "Reference: Snazzy Maps 'Tokyo Minimalist' (visual family only, not data source)",
      "Geographic data sourced from regional guides + OSM community validation"
    ]
  }
}
```

**Why:** Snazzy Maps re-interprets data aesthetically. Our maps do too, but we source our geographic facts separately.

---

## Gap 6: Delivery Contract Ambiguity

### Problem

Map Product Package doesn't specify exact deliverables. This creates downstream ambiguity.

### Fix: Define Deliverables Enum

#### Update Map Product Package Schema

```json
{
  "map_product_package": {
    "title": "Kyoto Neighborhoods: Geisha and Craft Districts",
    "subtitle": "An illustrated guide to three historic quarters",
    "product_type": "illustrated_narrative_map",
    "bundle_role": "hero",
    "publish_mode": "draft_only|qa_required|publish_ready",
    "deliverables": [
      "pdf_etsy_letter",
      "pdf_etsy_a4",
      "pdf_kdp_letter",
      "pdf_kdp_a4",
      "svg_master",
      "legend_pdf",
      "png_preview",
      "zip_bundle"
    ]
  }
}
```

#### Deliverables Enum Reference

| Code | Format | Purpose | Platform | Spec |
|------|--------|---------|----------|------|
| `pdf_etsy_letter` | PDF | Etsy-optimized | Etsy | 2550 × 3300 px, 300 DPI, US Letter |
| `pdf_etsy_a4` | PDF | Etsy-optimized | Etsy | 2480 × 3508 px, 300 DPI, A4 |
| `pdf_kdp_letter` | PDF | KDP-optimized | KDP | 2550 × 3300 px, 300 DPI, US Letter + bleed |
| `pdf_kdp_a4` | PDF | KDP-optimized | KDP | 2480 × 3508 px, 300 DPI, A4 + bleed |
| `svg_master` | SVG | Master file (editable layers, all elements) | Archive | Preserves all design decisions for future variants |
| `legend_pdf` | PDF | Legend/key standalone | Reference | 8.5 × 5.5 in, 300 DPI, can be printed separately |
| `png_preview` | PNG | Social/web preview | Social | 1200 × 800 px, RGB, web-optimized |
| `zip_bundle` | ZIP | Complete product package | Etsy/Archive | All PDF variants + SVG + PNG + legend + notes |

#### Rules for Deliverables Selection

**Batch 2 maps (Narrative, Neighborhood) — ALL deliverables:**
```json
{
  "deliverables": [
    "pdf_etsy_letter",
    "pdf_etsy_a4",
    "pdf_kdp_letter",
    "pdf_kdp_a4",
    "svg_master",
    "legend_pdf",
    "png_preview",
    "zip_bundle"
  ]
}
```

**Batch 3 maps (Complex, Premium) — Subset pending:**
```json
{
  "deliverables": [
    "pdf_etsy_letter",
    "pdf_etsy_a4",
    "svg_master",
    "legend_pdf",
    "png_preview"
  ],
  "notes": "KDP variants deferred; complex maps assessed for print suitability first"
}
```

**Mini/Entry maps (District inserts, simplified) — Minimal:**
```json
{
  "deliverables": [
    "pdf_etsy_letter",
    "pdf_etsy_a4",
    "png_preview",
    "zip_bundle"
  ],
  "notes": "No SVG master (simple, non-editable); no separate legend"
}
```

---

## Deployment Checklist

### Map Structure Agent

- [ ] Add `unused_candidates[]` to output contract
- [ ] For each area/POI not in final map, document:
  - item name
  - why excluded
  - brand fit assessment
  - suggested future home + notes
- [ ] Example test: Kyoto map excludes Imperial Palace → rehoming entry created

### Map QA Agent

- [ ] Add `rehoming_suggestions[]` to output contract
- [ ] For assets generated but unused, document with same structure
- [ ] Example test: Generated gold teacup icon unused → rehoming entry

### Map Packaging Agent

- [ ] Collect `unused_candidates` from Structure Agent
- [ ] Collect `rehoming_suggestions` from QA Agent
- [ ] Write to `rehoming_log.json` per G7 merge rule
- [ ] Validate: no duplicates (merge if found, append contributors)

### rehoming_log.json

- [ ] Create empty template in jobs/{job_id}/metadata/
- [ ] Update during packaging (append, never overwrite)
- [ ] Available for future curation queries ("what Kyoto items are waiting for homes?")

### Map Job Input

- [ ] Add `source_refs[]` with required fields:
  - title
  - type (book, guide, web, osm, interview)
  - confidence (high/medium/low)
  - relevance (what it supports)
- [ ] Add `source_mode_notes` explaining source strategy

### Map Structure Agent

- [ ] Accept `source_refs[]` from Job input
- [ ] Output `source_refs[]` showing which sources were used for which parts
- [ ] Output `needs_verification_items[]` flagging medium-confidence areas
- [ ] Example: Craft shops in Higashiyama flagged for spot-check

### Map Product Package

- [ ] Ensure `deliverables[]` is explicitly enumerated
- [ ] For Batch 2 maps: use full enum (8 items)
- [ ] For Batch 3 maps: justify reduced list
- [ ] For Entry maps: justify minimal list

---

## Success Criteria

✅ **No POI loss** — unused items logged with future homes  
✅ **Credible sourcing** — all facts traceable to editorial reference  
✅ **No generic tourism** — geographic choices tied to sources, not stereotypes  
✅ **Clear deliverables** — packaging agent knows exactly what to produce  
✅ **Batch 2 ready** — all 8 deliverables defined and producible  
✅ **Batch 3 deferred** — explicitly noted as "not yet publish-safe"
