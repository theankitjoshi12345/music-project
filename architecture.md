# Score Companion architecture

This document describes the implemented local application, including the
measure-image pipeline in [MR !26](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/merge_requests/26).

## System boundaries

Score Companion runs a React browser client and a Django REST Framework API.
SQLite stores score metadata, detected measures, extraction state, and practice
marks. Original uploads live on the backend filesystem. Audiveris and Poppler
run locally as subprocesses; there is no paid recognition API or deployed cloud
worker in the current implementation.

There are two supported startup options: native development with Vite and Django,
and Docker Compose with a built React frontend behind Nginx and a Gunicorn API.
Both use the same application code and recognition pipeline.

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

## Docker startup and service boundaries

From the repository root, `docker compose up --build -d --wait` builds and starts
the complete application at http://localhost:8080/. Docker is the only required
host runtime for this option. The Compose file defines:

| Service | Responsibilities | Network and storage |
| --- | --- | --- |
| frontend | Node build stage; Nginx serves the built React assets, original uploads and Django static files; proxies /api and /admin | Host port 8080 by default; read-only app-data mount |
| backend | Python 3.12, Django/Gunicorn, Poppler, Audiveris 5.11.0 and bundled Java | Internal port 8000 only; writable app-data mount |

The frontend starts after the backend health check succeeds. Both services have
health checks, and Compose's wait option checks API readiness through the proxy.
The port and bind address can be changed without editing application code.
The default bind address is 127.0.0.1; LAN use requires changing it and including
the private IP in Django's allowed hosts. No Vite server runs in Docker.

The backend uses the official checksum-verified Ubuntu 24.04 x86_64 Audiveris
installer. Its bundled Java and native libraries stay in the Linux image.
Because this release has no Linux ARM installer, Compose sets the backend
platform to linux/amd64. Apple Silicon Docker Desktop runs that service through
emulation; the frontend image is built for the host architecture.

The backend runs as an unprivileged app user. Its entrypoint creates persistent
media and static directories, generates a Django secret key once, applies
migrations, collects static files, and starts Gunicorn with one process and four
threads. Docker allows 600 seconds for Audiveris, with 720-second Gunicorn/Nginx
timeouts for the current synchronous recognition flow. Native development keeps
the 300-second Audiveris default. They do not introduce a background queue or a global OMR
concurrency limit. The JVM heap is capped at 1 GB and uses two logical processors.
Java runs headless with fixed display scaling so Audiveris skips GTK monitor
detection in the container. The build checks that its CLI starts as the app user.

The named app-data volume stores /data/db.sqlite3, /data/media, /data/static,
and /data/django-secret-key. Container replacement and Compose down preserve the
volume. Explicit volume removal erases this Docker state. Native development
continues to use backend/db.sqlite3 and backend/media by default, so the two
startup options can run concurrently with independent libraries.

Django settings accept DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, DJANGO_DATA_DIR,
DJANGO_SECRET_KEY and DJANGO_SECRET_KEY_FILE. The file setting takes precedence
when provided. Compose disables DEBUG and uses the generated secret file;
the native defaults retain the existing development behavior. Nginx serves media
and collected static files when DEBUG is false.

The build context excludes host data, the Mac .local-tools runtime, environment
files, virtual environments, node_modules and course reports. The source remains
the same checkout; the container gets its own Linux runtime. See
[third-party notices](THIRD_PARTY_NOTICES.md) for the installer and source links.

## User flow

1. Add a PDF or MusicXML score to Library. Reuploading identical file contents
   opens the existing score, including its measures and practice marks.
2. Open the score. PDFs without current layout data start recognition; the
   reader shows progress and a retry action on failure.
3. Select a detected measure number to load its original notation as a crop.
   Full page displays a rendered PDF page with selectable measure regions.
4. Save a measure with Save for practice. Practice Review lists the selected demo
   user's saved passages and can mark them resolved.
5. Open measure returns to the exact score and passage ID, selecting its page
   and measure image.
6. Remove from practice deletes the user's saved row and note. Deleting the
   score through Library's Score options removes the source and related records.

Library is shared between the demo users. Practice marks are isolated by the
X-Mock-User header (alex or sam in the UI). This header is a local demonstration
mechanism, not authentication or an access-control boundary. Screens remount when
the selected user or hash route changes so late responses cannot populate another
user's review or another score's reader.

## Navigation, loading and removal

All four screens use AppLayout and its shared Library/Practice review header.
The reader keeps measure navigation and the save/remove action next to the
selected notation. Full-page mode has separately labelled page controls. A
global measure jump and Left/Right keyboard handler change both page and selected
passage; the handler ignores editable fields and modifier shortcuts and stops
at score boundaries. Only the measure list scrolls when following a selection.
The native marker uses the same image endpoint and keyboard behavior. It is
reachable through Library's Score options, alongside the destructive score action.

LoadingSkeleton provides labelled, aria-busy placeholders for library, reader,
review, marker and notation reads. Placeholder shapes are hidden from assistive
technology, and animation respects reduced-motion preferences. Write actions
show pending button states; a failed request preserves the visible record.
Retry controls recover failed reads and image loads.

Passage responses include the current user's practice_mark_id. DELETE on the
practice-mark detail endpoint scopes the lookup to X-Mock-User, deletes the row
and its inline note, and returns 204. There is no separate practice-file store.
The reader and marker clear their saved flag/ID only after confirmation, while
Review removes the corresponding card. Reloading any screen fetches authoritative
state. Another user's practice row is retained; attempting its ID returns 404.
Removing a mark retains the library score/PDF. Score deletion removes the source
file and cascades its passages and every attached mark.

The browser walkthrough in frontend/e2e/workflow.mjs checks the complete UI path,
keyboard/input behavior, failure recovery, ownership, responsive layouts and
backend/file cleanup against an empty, separate library. See
[the usability review](docs/UI_REVIEW.md) for tasks and observed fixes.

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

SQLite and uploaded media are runtime state and are excluded from Git and Docker
builds. Native development stores them under backend; Compose stores them in the
app-data volume. Tests use separate database and media storage and do not populate
the user's library with sample files.

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
| processing | Shows an estimated countdown and elapsed time; readers poll the score |
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

### Conversion time estimate

The existing extraction_updated_at field records the claim time while a job is
processing; page-count updates do not change it. Score responses expose it as
extraction_started_at for an active job, avoiding a new persistence model.
The PDF inspection step publishes its real page count before rasterization and
recognition. The serializer estimates total duration as 15 seconds of setup plus
page count times OMR_ESTIMATED_SECONDS_PER_PAGE, capped at OMR_TIMEOUT_SECONDS.
The defaults are 15 seconds per page natively and 150 in Docker for emulation.
Operators can tune this estimate for their hardware; it is not measured OMR
progress and does not control the actual timeout.

The reader polls every 1.5 seconds even while its extraction POST is pending.
ExtractionProgress uses the server start time and updates its clock every second;
refreshing, remounting or polling therefore does not restart the countdown.
When the estimate expires it shows a longer-than-estimated message and keeps
counting elapsed time. Only completion/failure from the API ends the progress
state. Clock updates are outside the live status announcement to avoid reading
every second aloud. Spinning feedback respects reduced-motion preferences.
Library conversion/retry actions enter the reader immediately, and on phones
progress precedes the PDF image so it remains visible.

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
| Audiveris recognition | 300-second native timeout; 600 seconds in Docker for emulation headroom |
| One image render | 30-second timeout |

Native Audiveris discovery checks AUDIVERIS_COMMAND, then PATH, then the macOS application
paths configured in backend/config/settings.py. A mounted installer is not the
runtime. Local binaries under .local-tools are excluded from Git and must be
installed separately for native development on another machine. Docker sets
AUDIVERIS_COMMAND to /opt/audiveris/bin/Audiveris inside its backend image, so the
Docker host does not need a separate Audiveris, Java or Poppler installation.

Audiveris is an external AGPL-3.0 application; its source and license are available
in the [upstream repository](https://github.com/Audiveris/audiveris). No Audiveris
binary is committed to this repository. The Docker build downloads the official
installer and retains its license material in the resulting image.

## Implementation map

| Location | Responsibility |
| --- | --- |
| frontend/src/App.jsx | Hash routing and user/route screen isolation |
| frontend/src/OfflineScoreLibrary.jsx | Upload, reopen, extraction action, deletion |
| frontend/src/pages/useScoreViewer.js | Load score data, extraction progress, selection, practice saves |
| frontend/src/pages/PdfScoreReader.jsx | Measure images, full-page images, region selection, loading/error feedback |
| frontend/src/pages/ExtractionProgress.jsx, extractionTiming.js | Estimated countdown, elapsed time, overrun feedback and clock formatting |
| frontend/src/pages/useMeasureKeyboard.js, measureNavigation.js | Keyboard controls, form-field protection and measure boundaries |
| frontend/src/components/score-companion/LoadingSkeleton.jsx | Accessible placeholders for data and notation loads |
| frontend/src/PracticeReview.jsx | Review and resolve the selected user's practice marks |
| backend/scoreapi/models.py | Score, Passage, PracticeMark and constraints |
| backend/scoreapi/upload_service.py | Content deduplication and file/database cleanup |
| backend/scoreapi/extraction_service.py | Extraction claiming, retries and transactional passage import |
| backend/scoreapi/score_extract.py | MusicXML parsing, Audiveris invocation and layout import |
| backend/scoreapi/pdf_render.py | Original PDF page and measure PNG rendering |
| backend/scoreapi/views.py | API operations and image responses |
| backend/scoreapi/migrations/ | Persistent schema changes |
| Dockerfile, compose.yaml | Frontend/backend image builds, health checks, networking and persistent volume |
| docker/entrypoint.sh | First-run setup, migrations and Gunicorn startup |
| docker/nginx.conf | Built frontend, same-origin API proxy and persistent media/static serving |
| backend/config/settings.py | Native defaults and Docker environment overrides |

See [README.md](README.md) for startup and user testing, and
[API_CONTRACT.md](API_CONTRACT.md) for endpoint payloads and error responses.

## Verification and remaining boundaries

On November 3, 2026, both startup options passed browser acceptance with the real
two-page demo PDF. Native testing started fresh Django and Vite processes with an
isolated data directory. Docker testing built and started both Compose services,
then exercised the same flow through Nginx and Gunicorn with DEBUG disabled.
Both ran actual Audiveris recognition, clicked every detected measure, and loaded
all 56 distinct notation images. Both full-page images and their clickable
regions worked. Selected crops and browser screenshots were visually checked.

The browser check also saved and resolved a practice mark, returned from Practice
Review to its exact measure and page, verified demo-user isolation, reused an
identical upload without losing practice data, and deleted the disposable score,
its source file, passages, and marks. No browser exceptions or failed application
requests occurred in the passing acceptance runs. Compose down followed by a
fresh one-command startup preserved the exact PDF, all 56 passages, the resolved
practice mark and the generated secret key. The saved passage loaded in the
browser after recreation. Nginx served original PDFs and collected admin assets
with DEBUG disabled. Disposable test records were deleted afterward; the native
library stayed separate from test data. All 34 backend tests pass in both
runtimes; 23 frontend tests, migration checks and the production build pass.

Production authentication, durable cloud storage, cloud deployment, a background
queue, guaranteed OMR accuracy, actual offline browser caching, and note-level
music editing remain outside the implemented local demo.
