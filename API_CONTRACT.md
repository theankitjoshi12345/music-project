# Score Companion API Contract

**Status:** Implemented shared backend contract for the score library, reader,
measure marker, and practice review.

**Base URL:** http://127.0.0.1:8000/api for the native Django server, or
http://localhost:8080/api through Docker's Nginx frontend. The browser uses
same-origin /api requests in both setups; Vite proxies them during native
development. Docker does not publish the backend port separately.

**Format:** JSON request and response bodies; uploads use multipart form data.

**Identity and authorization:** Clients first call `GET /api/session/`. In local
`DJANGO_AUTH_MODE=demo`, scores are shared and `X-Mock-User` selects the practice
profile (`alex` or `sam` in the UI). In `DJANGO_AUTH_MODE=session`, a server-issued,
HttpOnly session cookie owns a private score library; `X-Mock-User` cannot change
that identity. Every score, original file, rendered image, passage and practice
operation checks this owner. Legacy NULL-owned local scores remain inaccessible
to public sessions. A missing session returns 403; another owner's object is
treated as absent (404, or a 400 invalid passage reference on mark creation).

Session mode is an anonymous browser identity, not a verified Google account.
Access lasts 30 days of inactivity and refreshes on requests. Losing cookies,
using another browser or letting the session expire loses access; there is no
account recovery or automatic deletion of the stored scores. Production requires
HTTPS and uses host-only `__Host-` cookies. `DJANGO_ENV=production` rejects demo
mode, DEBUG and insecure signing keys. The admin route is disabled by default.

Session-mode `POST`, `PATCH` and `DELETE` requests must include the session cookie
and `X-CSRFToken` using the `csrfToken` returned by session initialization. Missing
or invalid CSRF tokens and untrusted origins return 403, including for anonymous
users. Same-origin `fetch` sends cookies by default. File/image tags use the same
session cookie; direct `/media/` URLs must not be publicly served.

## Screen-to-endpoint map

| Screen owner | Screen | Endpoints |
| --- | --- | --- |
| Logan | Score Library | GET /scores/, POST /scores/upload/, GET/DELETE /scores/{id}/ |
| Ankit | Score Viewer & Navigation | GET/POST /scores/{id}/passages/, POST /practice-marks/, DELETE /practice-marks/{id}/, PDF image endpoints |
| Matthew | Measure Marker | GET /scores/{id}/passages/, POST /practice-marks/, DELETE /practice-marks/{id}/ |
| Jonathan | Practice Review | GET /practice-marks/, PATCH/DELETE /practice-marks/{id}/ |

## Data models and relationships

    BrowserSession 1 -- * Score 1 -- * Passage 1 -- * PracticeMark

Local demo mode retains the shared score library and separates practice marks by
selected profile. Public session mode scopes both scores and marks to the browser.

### Score

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Generated primary key |
| title | string | Score or work title |
| movement | string | Movement or part name |
| instrument | string | Instrument or section |
| page_count | integer | Positive total page count |
| available_offline | boolean | Offline-library availability |
| source_file | string or null | Authorized same-origin `/api/scores/{id}/file/` URL; never a raw storage path |
| source_type | string or null | `pdf`, `musicxml` (including XML/MXL), or null; use this to select the reader |
| extraction_started_at | string or null | ISO-8601 server start time for an active conversion; null when inactive, completed or interrupted |
| extraction_estimated_seconds | integer or null | Approximate total PDF conversion duration for this runtime and page count; null for non-PDF scores |

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
| is_marked_for_practice | boolean | Whether the current browser identity or local demo profile has a saved practice item |
| practice_mark_id | integer or null | That user's practice row ID, used for DELETE; another user's ID is never returned |

A score cannot have duplicate section and measure_number combinations.

Practice Review links to `#/score-viewer?score={score_id}&passage={id}` using
the nested passage object from a practice mark. The viewer opens the requested
passage's page, with the normal initial-page fallback for an unknown passage ID.

### PracticeMark

| Field | Type | Notes |
| --- | --- | --- |
| id | integer | Generated primary key |
| owner | string | Opaque server owner identifier, or local demo profile ID; response only and never an authentication credential |
| passage | object | Read-only passage context in responses |
| passage_id | integer | Required only when creating a mark |
| note | string | Optional, trimmed, maximum 500 characters |
| is_resolved | boolean | Defaults to false |
| created_at, updated_at | ISO 8601 string | Server-managed timestamps |

There can be one practice mark per passage for each owner. A mark cannot
be moved to a different passage after creation.

## Endpoints

### GET /api/health/

Returns the existing service check.

    {"status": "ok", "service": "score-companion-api"}

This is public liveness only. It does not expose account or library information
and is exempt from HTTPS redirects for internal container probes.

### GET /api/session/

Initializes or resumes the browser library and returns a CSRF token. The response
uses `Cache-Control: private, no-store` and never returns the private owner token.

    {
      "auth_mode": "session",
      "display_name": "Private browser library",
      "csrfToken": "<request-specific CSRF token>",
      "expires_in_seconds": 2592000
    }

Local demo mode returns `auth_mode: "demo"`, `display_name: "Local practice
profile"` and `expires_in_seconds: null`. Clients should finish this request
before loading scores or issuing concurrent uploads.

### GET /api/scores/

Lists only the current library's uploaded parts (shared local library in demo
mode; private browser library in session mode).

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

### GET /api/scores/{id}/file/

Serves the original upload after the same ownership check as score detail.
PDFs use `application/pdf` with inline disposition and `X-Frame-Options:
SAMEORIGIN`; MusicXML/XML/MXL downloads use `application/octet-stream` and
attachment disposition. Responses use `Cache-Control: private, no-store` and
`X-Content-Type-Options: nosniff`. Missing files and inaccessible scores return 404.

### DELETE /api/scores/{id}/

Removes an uploaded score, its local source file, all of its passages, and any
practice marks attached to those passages. Returns 204 No Content.

### POST /api/scores/{id}/extract-measures/

For a stored PDF (up to 10 pages), runs local Audiveris after rendering each page
with `pdftoppm`. Imported measures retain their PDF page numbers. Matching
passages are updated without deleting IDs or practice notes. Completed imports
are returned from storage. A host-wide file lock permits one Audiveris process
across workers. Returns 409 while another score is being converted (retry later)
or another request is processing the same score (poll its detail),
503 when the local runtime is unavailable, and 422 when recognition fails.

Before rasterization, `pdfinfo -box` verifies every extraction page's reported
size and uncropped MediaBox. Each side is limited to 1,440 points (20 inches)
and each page to 25 million pixels at 300 DPI. Page/measure image endpoints apply
the same check to the requested page even before recognition. Excessive pages
return 422 with a message asking for a standard Letter/A4 export; no rasterizer
is started for the rejected page or extraction batch.

Score responses include `extraction_status` (`not_started`, `processing`,
`complete`, or `failed`) and `extraction_error`. Clients may poll the score detail
while processing and retry after failure. The browser starts extraction after
a PDF upload and displays the returned passages next to the PDF.

While processing, `extraction_started_at` remains stable and
`extraction_estimated_seconds` is based on the real page count, published as soon
as PDF inspection finishes. The estimate is `15 + page_count *
OMR_ESTIMATED_SECONDS_PER_PAGE`, capped at the configured recognition timeout.
The per-page default is 15 seconds natively and 150 seconds in Docker, where
Intel emulation can be slower. These are planning estimates, not measured
recognition percentages or completion deadlines. Clients poll during their own
long-running POST as well as when opening an already-running conversion.
At zero remaining time the UI continues showing elapsed time and a longer-than-
estimated message; success/failure comes from the server's extraction status.
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

MusicXML parsing rejects entity expansion and external entities. Plain XML and
the selected uncompressed MXL score are limited to 20 MiB; MXL manifests to 64
KiB before decompression; archives to 1,000 entries; and imported scores to
10,000 measures. Invalid or excessive inputs return 400 without saving a score.
Ordinary MusicXML DOCTYPE declarations remain supported without fetching a DTD.

Public session-mode quotas default to 20 scores/100 MiB per browser and 100
scores/500 MiB across public libraries. Exceeding a score or uploaded-byte limit
returns 429 with a user-readable `detail` before saving a new file. Duplicate
uploads within the same library remain allowed. The persistent-host upload lock
serializes quota checks and file creation across workers. The limits are
configured by `PUBLIC_MAX_SCORES_PER_SESSION`, `PUBLIC_MAX_BYTES_PER_SESSION`,
`PUBLIC_MAX_SCORES_TOTAL` and `PUBLIC_MAX_BYTES_TOTAL`; they count original uploads,
not temporary OMR work space. Local demo mode does not apply these public quotas.

New files return 201 with `already_uploaded: false`. Identical file contents
within the same owner scope return the original score with 200 and
`already_uploaded: true`; original
metadata, extracted measures, and practice marks are preserved. Different file
contents get separate storage paths, even when filenames match. Existing local
files can be indexed once with `manage.py index_score_files` after migration.
The same file uploaded by another browser creates an independent file and score;
its existence, metadata and practice notes are not disclosed across libraries.

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

### DELETE /api/practice-marks/{id}/

Permanently removes the current owner's practice row and its note. Returns
204 with no response body. An absent ID or an ID owned by someone else
returns 404. The score, source PDF, passages, and other owners' marks are
retained. Practice marks reference existing passages and do not create PDF copies.

The frontend updates the saved state only after a successful DELETE (or a 404
confirming the item is already absent). Passage responses then contain
is_marked_for_practice=false and practice_mark_id=null for that user. Failures
keep the displayed item and allow retry. Deleting a score still removes its
source file and cascades all its passages and marks.

## Validation and errors

| Situation | Status | Example response |
| --- | ---: | --- |
| Missing score, passage, or mark | 404 | {"detail": "Not found."} |
| Missing browser session | 403 | Initialize `/api/session/` first |
| Missing/invalid CSRF or untrusted origin | 403 | CSRF validation detail |
| Public upload quota exceeded | 429 | User-readable `detail` |
| Recognition worker busy | 409 | Retry later; current score remains retryable |
| Missing passage_id on create | 400 | {"passage_id": ["This field is required."]} |
| Nonexistent passage | 400 | {"passage_id": ["Invalid pk ..."]} |
| Duplicate mark for a passage | 200 | Existing mark (idempotent save) |
| Note over 500 characters | 400 | Field-level validation error |
| Attempt to move a mark | 400 | {"passage_id": ["A practice mark cannot be moved to another passage."]} |
| Invalid review status | 400 | {"status": "Use 'unresolved' or 'resolved'."} |

The API does not yet provide verified Google sign-in, cross-device account
recovery, tuner/metronome tools, social features or automatic musical-error
detection. Deployment and persistence status are recorded in the root README;
session support alone does not establish that a public deployment exists.
