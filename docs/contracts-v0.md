# Contracts v0 (Raimon) — Text → Structure + Suggestions + Dedupe

**Owner (Part 0): Earth 3 (Mark / Epowei)**  
**Purpose:** Provide stable data contracts so Earth 1 (UX/agent) and Earth 2 (backend/rhythm) can build without ambiguity.  
**Change policy:** Cross-part changes require a single post in `#decision-ledger` + update this doc (and re-pin the updated contract if needed).

---

## 0) Scope (v0) and non-goals

### In scope
- Text → structured “idea” classification output
- Unified “suggestions queue” item shape (manual ideas + future integrations)
- Initial `TaskType` enum
- Dedupe strategy v0 (rules + normalization + hashing)

### Non-goals (for v0)
- Final DB schema (Earth 2 owns Part 2 schema contracts)
- Final integration payload shapes (Earth 2 owns Part 3 selection/providers)
- A perfect ontology of task types (we start coarse, expand later)

---

## 1) TaskType enum (v0)

Used for: routing, UX labels, rhythm learning, scoring.

```json
{
  "TaskType": [
    "ADMIN",
    "DEEP_WORK",
    "CREATIVE",
    "COMMUNICATION",
    "PLANNING",
    "ERRAND",
    "PERSONAL",
    "LEARNING",
    "HEALTH",
    "UNKNOWN"
  ]
}
```

Notes
- UNKNOWN is valid output.

- Don’t rename existing values; only add new ones.

- Use taskType as a hint (not a hard rule) for the NextDo engine.

## 2) IdeaClassification (v0)

### When used
Part 1 brain-dump capture → parse into structured fields and suggest where it belongs.

### Output
One record per user-provided idea line (or per chunk if multi-idea input is split).

### Required fields (v0)
- `rawText`
- `normalizedText`
- `taskType`
- `isActionable`
- `confidence`
- `createdAt`

### Optional fields
- `suggestedProject` (recommended)
- `suggestedDo` (only if `isActionable=true`)
- `entities`, `tags`

### JSON shape
```json
{
  "IdeaClassification": {
    "id": "ic_<ulid>",
    "rawText": "Book dentist appointment next week",
    "normalizedText": "Book dentist appointment",
    "confidence": 0.78,
    "taskType": "PERSONAL",
    "isActionable": true,
    "suggestedProject": {
      "projectId": null,
      "projectTitle": "Health",
      "confidence": 0.64
    },
    "suggestedDo": {
      "title": "Call dentist to book appointment",
      "estMinutes": 10,
      "context": "phone",
      "dueDate": "2026-01-27",
      "blockers": []
    },
    "entities": {
      "people": [],
      "places": [],
      "tools": [],
      "urls": [],
      "dates": ["next week"]
    },
    "tags": ["health"],
    "createdAt": "2026-01-20T10:15:00Z"
  }
}
```

### Behavioral rules (v0)
- If `isActionable=false`, omit `suggestedDo` or set it to `null`.
- `dueDate` may be `null` if unknown.
- If no project match, set `suggestedProject.projectTitle` to `"Inbox"`.
- `confidence` is a float in **[0, 1]** and represents **parser confidence** (not user confidence).

---

## 3) SuggestionItem (v0)

Unified suggestion queue item used for:
- Part 1 internal suggestions (“Convert idea to Do”)
- Part 3 integration imports (later)

### Required fields (v0)
- `id`
- `source`
- `title`
- `taskType`
- `actionability`
- `dedupe`
- `createdAt`

### Enums

```json
{
  "SuggestionSource": ["MANUAL_IDEA", "SYSTEM", "INTEGRATION"],
  "PriorityHint": ["LOW", "MEDIUM", "HIGH"],
  "Actionability": ["READY", "NEEDS_INFO", "BLOCKED"],
  "DedupeStatus": ["UNIQUE", "DUPLICATE_DROPPED", "NEEDS_REVIEW"]
}
```

### JSON shape

```json
{
  "SuggestionItem": {
    "id": "sug_<ulid>",
    "source": "MANUAL_IDEA",
    "sourceAccountId": null,
    "externalId": null,

    "title": "Call dentist to book appointment",
    "body": "User mentioned booking next week; propose quick call.",
    "taskType": "PERSONAL",

    "suggestedProjectTitle": "Health",
    "estMinutes": 10,
    "dueDate": "2026-01-27",
    "priorityHint": "MEDIUM",
    "actionability": "READY",

    "dedupe": {
      "contentHash": "sha256:<computed>",
      "candidateKeys": [
        "title_norm:call dentist book appointment",
        "date:2026-01-27",
        "project:health"
      ],
      "status": "UNIQUE",
      "duplicateOfId": null
    },

    "raw": {
      "originalText": "Book dentist appointment next week"
    },
    "createdAt": "2026-01-20T10:16:00Z"
  }
}
```

### Notes
- `raw` is an escape hatch for original text/payload (especially for integrations later).
- `dedupe.contentHash` is mandatory (cheap dedupe that works now).
- `sourceAccountId` is for integration account scoping (e.g., a user’s Google account). Keep `null` for manual/system suggestions.

---

## 4) Dedupe strategy v0 (priority order)

**Goal:** prevent duplicates across repeated capture/imports/syncs without blocking product flow.

### 4.1 Match hierarchy

**Level 1 — External identity (integration only, Part 3):**
1) If `source=INTEGRATION` **AND** `externalId` matches for the same `sourceAccountId` → duplicate (**hard match**)

**Level 2 — Deterministic content matching (works now):**
2) If `dedupe.contentHash` matches → duplicate (**hard match**)  
3) If `title_norm` matches **AND** `dueDate` matches (or both `null`) → duplicate (**hard match**)

**Level 3 — Optional semantic fallback (can be added later):**
4) If same `taskType` **AND** embedding similarity(title) ≥ 0.88 **AND** due dates within ±2 days → likely duplicate  
   - set `dedupe.status="NEEDS_REVIEW"` (do not auto-drop in v0 unless product decides it’s safe)

### 4.2 Normalization spec

**normalize(text):**
- lowercase
- trim
- collapse whitespace
- remove punctuation

**Example:**
- `"Call dentist to book appointment!"` → `"call dentist to book appointment"`

### 4.3 Hashing spec

Compute `dedupe.contentHash` from this input string:

- `normalize(title) + "|" + (dueDate or "") + "|" + normalize(suggestedProjectTitle or "")`

Then:
- `sha256(input_string)` encoded as `sha256:<hex>`

### 4.4 Dedupe status behavior

**Recommended behavior:**
- If hard match (Level 1–2): set `dedupe.status="DUPLICATE_DROPPED"` and `duplicateOfId=<existing>`
- If semantic likely duplicate (Level 3): set `dedupe.status="NEEDS_REVIEW"` and surface only if user asks for “show all” or a review UI exists

---

## 5) Change process (Contracts governance)

If changes affect another Part: post once in `#decision-ledger`, then update this doc in the same PR.

Prefer backward compatibility:
- ✅ add optional fields
- ✅ add enum values
- ❌ rename/remove fields
- ❌ change meanings of existing fields without a migration plan

After merge: re-pin/update the Slack `#contracts` pinned message if needed.