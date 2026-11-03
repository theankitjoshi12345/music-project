# Score Companion architecture

This document describes the implemented local application, including the
measure-image pipeline in [MR !26](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/merge_requests/26).

## System boundaries

Score Companion runs a React/Vite browser client and a Django REST Framework API.
SQLite stores score metadata, detected measures, extraction state, and practice
marks. Original uploads live on the backend filesystem. Audiveris and Poppler
run locally as subprocesses; there is no paid recognition API or deployed cloud
worker in the current implementation.

~~~mermaid
flowchart LR
    Browser["React reader and library"]
    API["Django REST API"]
    DB[("SQLite")]
    Files[("Original uploaded files")]
    Poppler["Poppler: PDF pages and crops"]
    OMR["Audiveris: MusicXML and layout"]
    Browser -->|"JSON requests"| API
    Browser -->|"PNG image requests"| API
    API --> DB
    API --> Files
    Files --> Poppler
    Poppler -->|"300 dpi page images"| OMR
    OMR -->|"Measure metadata and coordinates"| API
    Poppler -->|"Original notation as PNG"| API
~~~

During development Vite serves the browser on port 5173 and proxies both /api
and /media to Django at 127.0.0.1:8000. The browser therefore uses one origin,
including when opening the app through Vite's private-network address.

## User flow

1. Add a PDF or MusicXML score to Library. Reuploading identical file contents
   opens the existing score, including its measures and practice marks.
2. Open the score. PDFs without current layout data start recognition; the
   reader shows progress and a retry action on failure.
3. Select a detected measure number to load its original notation as a crop.
   Full page displays a rendered PDF page with selectable measure regions.
4. Save a measure with + Practice. Practice Review lists the selected demo
   user's saved passages and can mark them resolved.
5. Open passage returns to the exact score and passage ID, selecting its page
   and measure image.

Library is shared between the demo users. Practice marks are isolated by the
X-Mock-User header (alex or sam in the UI). This header is a local demonstration
mechanism, not authentication or an access-control boundary. Screens remount when
the selected user or hash route changes so late responses cannot populate another
user's review or another score's reader.

## Data model and persistence

| Record | Stored data | Identity and relationships |
| --- | --- | --- |
| Score | Title, movement, instrument, page count, source file, SHA-256 content fingerprint, extraction state/error/time, layout version | One score has many passages; a non-null content fingerprint is unique |
| Passage | Section, measure number, original PDF page, optional bounding box | Belongs to one score; score + section + measure number is unique |
| PracticeMark | Mock owner, note, resolved state, timestamps | Belongs to a passage; passage + owner is unique |

A passage bounding box contains normalized x, y, width, and height, plus the
recognition image's pixel width and height. The region covers the measure stack
across all staves in its system, so a piano preview includes both hands.

The application does not implement MuseScore's complete Score/Measure/Segment/
Event hierarchy or a music engraving engine. Passage is the current measure-level
record. PDF notation is rendered from the original file, not reconstructed from
detected notes.

### Upload safety

- Upload size is limited to 10 MB. Accepted extensions are PDF, MusicXML, XML,
  and MXL.
- A SHA-256 fingerprint identifies identical file bytes. Repeated uploads return
  the existing score without changing its metadata or starting another import.
- New files use UUID storage names, so different contents with the same original
  filename cannot overwrite one another.
- Score and passage database writes are atomic. If an import fails, or an
  identical concurrent upload wins, the unused newly written file is removed.
- Existing uploads can be indexed with manage.py index_score_files. The command
  does not merge or delete existing score records.
- Deleting a score removes its original source file, its passages, and the
  passages' practice marks. Repeated practice saves return the existing mark.
- Repeated manual passage creation returns the existing passage on the same page.
  A conflicting page returns 409; an out-of-range page returns 400.

SQLite and backend/media are local state and are excluded from Git. Tests use a
temporary media directory and do not populate the live library with sample files.

## PDF recognition and layout import

Recognition is coordinated by extraction_service.py and implemented by
score_extract.py:

1. Read the PDF page count with pdfinfo and reject PDFs over the demo limit.
2. Render its pages at 300 dpi with pdftoppm into a temporary work directory.
3. Run Audiveris in batch mode with save, transcribe, and export enabled.
4. Import MusicXML measure metadata and read the corresponding .omr layout.
   Audiveris measure-stack IDs are matched to exported measure numbers.
5. Derive each crop's horizontal bounds from the stack and vertical bounds from
   the system's staves, adding notation padding. Store normalized coordinates
   relative to the original recognition image.
6. Upsert passages in a database transaction. Matching passages keep their IDs,
   so existing practice notes and links survive re-extraction.
7. Save the page count and current layout version, then discard the temporary
   rendered pages and Audiveris output files.

PDF pages are processed separately by Audiveris. Imported passages receive
sequential measure numbers across the document and Page N sections. Numbering
and boundaries are recognition estimates and should be checked against the score.
The importer rejects a missing page export or missing measure position instead
of silently assigning that music to a different page.

MusicXML/XML/MXL uploads bypass PDF recognition and import metadata from the first
score-partwise part. They do not currently produce original-PDF measure crops;
their existing metadata view uses illustrative notation.

### Extraction lifecycle

| State | Reader behavior |
| --- | --- |
| not_started | Starts PDF recognition when opened |
| processing | Shows progress; other readers can poll the score |
| complete | Uses saved measures and layout coordinates |
| failed | Shows the stored error and offers retry |

A conditional database update allows one active extraction request per score.
An additional request for that score returns 409 while recognition is active.
After the configured timeout plus 90 seconds, an interrupted processing state is
presented as a retryable failure.

A completed PDF import with layout version 0 contains metadata only. Opening it
prepares the layout coordinates; version 1 means measure positions were stored.
Completed imports with current layout data are reused. Failed extraction leaves
existing passages and practice marks intact.

This is synchronous processing in the Django request, not a durable job queue.
Different scores can still run concurrently; a public deployment would need
worker-level concurrency controls and an appropriate request timeout.

## PDF and measure rendering

pdf_render.py calls Poppler against the stored original PDF:

| Request | Rendering behavior |
| --- | --- |
| GET /api/scores/{id}/pages/{page}/image/ | Full page PNG at 150 dpi |
| GET /api/passages/{id}/preview/ | Measure crop at 300 dpi, using stored coordinates |

The reader loads PNGs as ordinary browser images rather than depending on a
browser PDF plugin to jump to a measure. Selecting a passage changes the image
URL and selected-measure heading. Full-page overlay positions use the same
normalized boxes as the crop endpoint.

Preview URLs include a geometry hash so changed crop bounds do not reuse stale
browser images. Responses allow private browser caching for five minutes. PNGs
are generated on request; there is no persistent preview-image store or server
render cache. The original PDF remains available through Open PDF.

Rendering checks the page or region before invoking Poppler and returns a clear
error when a source file or measure position is unavailable. Local /media serving
permits same-origin embedding.

## Runtime requirements and limits

| Component or operation | Current requirement or limit |
| --- | --- |
| Backend | Python 3.12+, Django and Django REST Framework from requirements.txt |
| Frontend | Node.js LTS and dependencies from frontend/package-lock.json |
| PDF tools | Poppler: pdfinfo and pdftoppm available on PATH |
| Recognition | Local Audiveris executable; 5.11 tested with its bundled Java runtime |
| PDF recognition | Maximum 10 pages |
| Page-count inspection | 15-second timeout |
| PDF rasterization | 60-second timeout |
| Audiveris recognition | 300-second timeout |
| One image render | 30-second timeout |

Audiveris discovery checks AUDIVERIS_COMMAND, then PATH, then the macOS application
paths configured in backend/config/settings.py. A mounted installer is not the
runtime. Local binaries under .local-tools are excluded from Git and must be
installed separately on another machine.

Audiveris is an external AGPL-3.0 application; its source and license are available
in the [upstream repository](https://github.com/Audiveris/audiveris). No Audiveris
binary is bundled in this repository.

## Implementation map

| Location | Responsibility |
| --- | --- |
| frontend/src/App.jsx | Hash routing and user/route screen isolation |
| frontend/src/OfflineScoreLibrary.jsx | Upload, reopen, extraction action, deletion |
| frontend/src/pages/useScoreViewer.js | Load score data, extraction progress, selection, practice saves |
| frontend/src/pages/PdfScoreReader.jsx | Measure images, full-page images, region selection, loading/error feedback |
| frontend/src/PracticeReview.jsx | Review and resolve the selected user's practice marks |
| backend/scoreapi/models.py | Score, Passage, PracticeMark and constraints |
| backend/scoreapi/upload_service.py | Content deduplication and file/database cleanup |
| backend/scoreapi/extraction_service.py | Extraction claiming, retries and transactional passage import |
| backend/scoreapi/score_extract.py | MusicXML parsing, Audiveris invocation and layout import |
| backend/scoreapi/pdf_render.py | Original PDF page and measure PNG rendering |
| backend/scoreapi/views.py | API operations and image responses |
| backend/scoreapi/migrations/ | Persistent schema changes |

See [README.md](README.md) for startup and user testing, and
[API_CONTRACT.md](API_CONTRACT.md) for endpoint payloads and error responses.

## Verification and remaining boundaries

A Playwright browser acceptance check uploaded the real two-page demo PDF into
an isolated database and ran actual Audiveris recognition. It clicked every
detected measure and verified all 56 distinct notation images loaded. Both
full-page images and their clickable measure regions worked. Selected crops
were visually compared with the original notation.

The browser check also saved and resolved a practice mark, returned from Practice
Review to its exact measure and page, verified demo-user isolation, reused an
identical upload without losing practice data, and deleted the disposable score,
its source file, passages, and marks. No browser exceptions or failed application
requests occurred. The user's database and uploads were kept separate from this
fresh-upload check. All 30 backend tests, 17 frontend tests, migration checks,
and the production build pass.

Production authentication, durable cloud storage, cloud deployment, a background
queue, guaranteed OMR accuracy, actual offline browser caching, and note-level
music editing remain outside the implemented local demo.
