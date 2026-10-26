# Score Companion API Contract

**Status:** Implemented on the 28-shared-api-contract feature branch. This is the shared backend contract for the P#9 React screens.

**Base URL:** http://127.0.0.1:8000/api

**Format:** JSON request and response bodies
**Authentication:** None for the P#9 local-development API.

## Screen-to-endpoint map

| Screen owner | Screen | Endpoints |
| --- | --- | --- |
| Logan | Offline Score Library | GET /scores/, GET /scores/{id}/ |
| Ankit | Score Viewer & Navigation | GET /scores/{id}/, GET /scores/{id}/passages/ |
| Matthew | Measure Marker | GET /scores/{id}/passages/, POST /practice-marks/ |
| Jonathan | Practice Review | GET /practice-marks/, PATCH /practice-marks/{id}/ |

## Data models and relationships

    Score 1 -- * Passage 1 -- 0..1 PracticeMark

### Score

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Generated primary key |
| title | string | Score or work title |
| movement | string | Movement or part name |
| instrument | string | Instrument or section |
| page_count | integer | Positive total page count |
| available_offline | boolean | Offline-library availability |

### Passage

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Generated primary key |
| score | integer | Parent score |
| section | string | Musical section, such as B |
| measure_number | integer | Positive measure number |
| page_number | integer | Positive score page number |
| movement | string | Included in practice-mark passage context for review display |
| score_id | integer | Included in practice-mark passage context so Open passage targets the correct score |

A score cannot have duplicate section and measure_number combinations.

Practice Review links to `#/score-viewer?score={score_id}&passage={id}` using
the nested passage object from a practice mark. The viewer opens the requested
passage's page, with the normal initial-page fallback for an unknown passage ID.

### PracticeMark

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Generated primary key |
| passage | object | Read-only passage context in responses |
| passage_id | integer | Required only when creating a mark |
| note | string | Optional, trimmed, maximum 500 characters |
| is_resolved | boolean | Defaults to false |
| created_at, updated_at | ISO 8601 string | Server-managed timestamps |

There can be only one practice mark per passage. A mark cannot be moved to a different passage after creation.

## Endpoints

### GET /api/health/

Returns the existing service check.

    {"status": "ok", "service": "score-companion-api"}

### GET /api/scores/

Lists downloaded parts for the Offline Score Library.

    [
      {
        "id": 1,
        "title": "Symphony No. 1",
        "movement": "Movement I",
        "instrument": "Percussion",
        "page_count": 4,
        "available_offline": true,
        "passage_count": 8
      }
    ]

### GET /api/scores/{id}/

Returns one score and its library/viewer context. A missing score returns 404 Not Found.

### GET /api/scores/{id}/passages/

Returns passages for the requested score in page/measure order. Used by the Score Viewer and Measure Marker.

    [
      {
        "id": 24,
        "section": "B",
        "measure_number": 24,
        "page_number": 2,
        "is_marked_for_practice": false
      }
    ]

### GET /api/practice-marks/

Lists saved practice marks for Practice Review.

Optional query parameters:

- score={id} limits marks to a score.
- status=unresolved or status=resolved filters the review state.

### POST /api/practice-marks/

Creates the explicit Mark for practice state.

    {
      "passage_id": 24,
      "note": "Keep the rhythm even through the transition."
    }

Returns 201 Created:

    {
      "id": 8,
      "passage": {
        "id": 24,
        "section": "B",
        "measure_number": 24,
        "page_number": 2,
        "is_marked_for_practice": true,
        "movement": "Movement I"
      },
      "note": "Keep the rhythm even through the transition.",
      "is_resolved": false,
      "created_at": "2026-10-23T18:00:00Z",
      "updated_at": "2026-10-23T18:00:00Z"
    }

### PATCH /api/practice-marks/{id}/

Updates the practice note and/or resolved status. This supports adding a note now or later and the resolved confirmation flow.

    {
      "note": "Keep the rhythm even through the transition.",
      "is_resolved": true
    }

Returns the updated practice-mark representation with 200 OK.

## Validation and errors

| Situation | Status | Example response |
| --- | ---: | --- |
| Missing score, passage, or mark | 404 | {"detail": "Not found."} |
| Missing passage_id on create | 400 | {"passage_id": ["This field is required."]} |
| Nonexistent passage | 400 | {"passage_id": ["Invalid pk ..."]} |
| Duplicate mark for a passage | 400 | Field-level validation error |
| Note over 500 characters | 400 | Field-level validation error |
| Attempt to move a mark | 400 | {"passage_id": ["A practice mark cannot be moved to another passage."]} |
| Invalid review status | 400 | {"status": "Use 'unresolved' or 'resolved'."} |

The API deliberately excludes authentication, cloud synchronization, file/PDF storage, tuner/metronome tools, social features, and automatic error detection.
