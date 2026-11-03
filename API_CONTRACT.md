# Score Companion API Contract

**Status:** Implemented shared backend contract for the score library, reader,
measure marker, and practice review.

**Base URL:** http://127.0.0.1:8000/api for the native Django server, or
http://localhost:8080/api through Docker's Nginx frontend. The browser uses
same-origin /api requests in both setups; Vite proxies them during native
development. Docker does not publish the backend port separately.

**Format:** JSON request and response bodies
**Mock authentication:** The local app sends the selected demo user in the
`X-Mock-User` request header. Supported demo users are `alex` and `sam`.
This is a structural placeholder for local multi-user flows, not production
authentication.

## Screen-to-endpoint map

| Screen owner | Screen | Endpoints |
| --- | --- | --- |
| Logan | Offline Score Library | GET /scores/, POST /scores/upload/, GET /scores/{id}/ |
| Ankit | Score Viewer & Navigation | GET/POST /scores/{id}/passages/, POST /practice-marks/ |
| Matthew | Measure Marker | GET /scores/{id}/passages/, POST /practice-marks/ |
| Jonathan | Practice Review | GET /practice-marks/, PATCH /practice-marks/{id}/ |

## Data models and relationships

    User 1 -- * PracticeMark * -- 1 Passage * -- 1 Score

### Score

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Generated primary key |
| owner | string | Mock-user ID that owns this mark; response only |
| title | string | Score or work title |
| movement | string | Movement or part name |
| instrument | string | Instrument or section |
| page_count | integer | Positive total page count |
| available_offline | boolean | Offline-library availability |
| source_file | string | Locally stored uploaded file path, when supplied |

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
| bounding_box | object or null | Normalized x/y/width/height and recognition image dimensions for the actual PDF measure |
| preview_url | string or null | PNG crop of the original notation; null until layout extraction is complete |

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

There can be one practice mark per passage for each mock user. A mark cannot
be moved to a different passage after creation.

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

### DELETE /api/scores/{id}/

Removes an uploaded score, its local source file, all of its passages, and any
practice marks attached to those passages. Returns 204 No Content.

### POST /api/scores/{id}/extract-measures/

For a stored PDF (up to 10 pages), runs local Audiveris after rendering each page
with `pdftoppm`. Imported measures retain their PDF page numbers. Matching
passages are updated without deleting IDs or practice notes. Completed imports
are returned from storage. Returns 409 while another request is processing,
503 when the local runtime is unavailable, and 422 when recognition fails.

Score responses include `extraction_status` (`not_started`, `processing`,
`complete`, or `failed`) and `extraction_error`. Clients may poll the score detail
while processing and retry after failure. The browser starts extraction after
a PDF upload and displays the returned passages next to the PDF.
The importer retains Audiveris measure-stack geometry. `measure_layout_version`
is 1 after these regions are stored. Older imports with version 0 are upgraded
on the next extraction, preserving passage IDs and practice notes.

### GET /api/passages/{id}/preview/

Renders the selected measure's notation from the original PDF as image/png.
Returns 409 when no saved region exists, 404 for an unknown passage, and 422
when the original PDF cannot render. The serialized URL includes a geometry
version query so updated crops cannot reuse an older browser-cached image.

### GET /api/scores/{id}/pages/{page_number}/image/

Renders one complete PDF page as image/png for consistent in-app viewing and
measure overlays. A page outside the score returns 404.

### POST /api/scores/upload/

Accepts multipart form data with `score_file` (PDF, MusicXML, XML, or MXL),
plus optional `instrument`, `title`, `movement`, and `page_count`. Files are
limited to 10 MB. MusicXML/XML/MXL inputs extract measures, rehearsal labels,
and MusicXML page breaks into Passages. PDFs are stored first; the browser then
starts recognition through `/scores/{id}/extract-measures/` and displays progress
in the reader.

New files return 201 with `already_uploaded: false`. Identical file contents
return the original score with 200 and `already_uploaded: true`; original
metadata, extracted measures, and practice marks are preserved. Different file
contents get separate storage paths, even when filenames match. Existing local
files can be indexed once with `manage.py index_score_files` after migration.

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

### POST /api/scores/{id}/passages/

Adds one visible measure to a score, primarily for manually mapping a PDF.

    {"section": "B", "measure_number": 24, "page_number": 2}

Repeated saves of the same section, measure, and page return the existing passage
with 200. New passages return 201. A different page for an existing measure
returns 409; a page outside the score returns 400.

### GET /api/practice-marks/

Lists saved practice marks for Practice Review.

Optional query parameters:

- score={id} limits marks to a score.
- status=unresolved or status=resolved filters the review state.

### POST /api/practice-marks/

Creates the explicit Mark for practice state. Repeated saves return the existing
mark with 200 OK, keeping its note and resolved state; new saves return 201.

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
| Duplicate mark for a passage | 200 | Existing mark (idempotent save) |
| Note over 500 characters | 400 | Field-level validation error |
| Attempt to move a mark | 400 | {"passage_id": ["A practice mark cannot be moved to another passage."]} |
| Invalid review status | 400 | {"status": "Use 'unresolved' or 'resolved'."} |

The API deliberately excludes production authentication, cloud synchronization,
PDF optical-music recognition, tuner/metronome tools, social features, and
automatic error detection.
