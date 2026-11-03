# Score Companion

Score Companion is a CMPS 453 team project for uploading sheet music, viewing
individual measures, and saving passages and notes for practice.

## P#10 local MVP

The app includes Logan's Offline Score Library, Ankit's Score Viewer & Navigation,
Matthew's Measure Marker, and Jonathan's Practice Review. The current flow is:
upload a score, select a measure, save it for practice, then review it or return
to its original score context. Despite the original screen name, browser offline
caching is not implemented.

The app uses local mock authentication, not production security. Choose **Alex Rivera** or **Sam Lee** in the Demo user selector. Practice marks are isolated by the selected mock user so the same passage can be marked independently for each demo user.

Use **Add to library** to upload a PDF, MusicXML, XML, or MXL file (up to 10 MB).
PDF uploads open the reader and start local Audiveris recognition automatically.
Detected measures appear next to the PDF, grouped by page. Use **+ Practice** to
save a measure, then **Practice review** to revisit it. Selecting a measure opens
its actual music cropped from the uploaded PDF, including all instrument staves
in that measure. **Full page** displays the original page with clickable measure
regions. Check recognition boundaries and numbering against the original score.
MusicXML/XML/MXL uploads import structured metadata directly.

The reader reports extraction progress and provides a retry action on failure. Use
**Delete score** to remove an uploaded score, its local file, its measures, and
any practice marks attached to those measures.

Uploading an identical file reopens its existing library entry and keeps its
measures and practice notes. Different files with the same original filename
are stored separately. Database failures clean up the newly written file.

Uploaded PDFs display directly in the Score Viewer. Use the viewer page controls
to move through the document or open the original PDF in a new tab.
Existing PDFs imported without page coordinates automatically prepare previews
when opened. Existing practice marks retain their passage IDs during this upgrade.

### PDF recognition and rendering

PDF measure recognition requires local Poppler (`pdftoppm` and `pdfinfo`) and
Audiveris. Page and measure images also require Poppler. Set `AUDIVERIS_COMMAND`
to the executable, or install it on PATH. On macOS the app also checks
`/Applications/Audiveris.app` and `.local-tools/Audiveris.app` in this checkout.
The mounted installer is not used as the runtime. The binary is local-only and
excluded from Git; a new deployment must install it separately.

The demo limits recognition to PDFs with at most 10 pages and bounds rendering
and recognition time. A second request for the same score shares the processing
state; completed imports are reused. Failed/repeated extraction preserves
existing measures and practice notes. Audiveris is an external AGPL-3.0 application;
see its [source and license](https://github.com/Audiveris/audiveris).

## Tech stack

| Area | Choice |
| --- | --- |
| Frontend | React + Vite (JavaScript) |
| Backend | Django + Django REST Framework |
| Database | SQLite |
| Runtime | Python 3.12+ and Node.js LTS |
| PDF pipeline | Poppler + local Audiveris; original PDF crops rendered as PNG |
| Version control | GitLab merge requests + GitHub mirror |
| UI reference | [Score Companion Figma design](https://www.figma.com/design/NSZliKsVC3CiwrjqQfrOHS) and export: `p9/Score_Companion_P8_Revised_Screens.pdf` |

See [architecture.md](architecture.md) for the implemented data flow, persistence,
runtime limits, and remaining boundaries.

## Screen ownership

| Owner | Assigned screen | Complexity | Route |
| --- | --- | --- | --- |
| Ankit Joshi | Score Viewer & Navigation | Hardest | [`#/score-viewer`](http://localhost:5173/#/score-viewer) |
| Matthew Pisani | Measure Marker | Hard | [`#/measure-marker`](http://localhost:5173/#/measure-marker) |
| Jonathan Dempsey | Practice Review | Medium | [`#/practice-review`](http://localhost:5173/#/practice-review) |
| Logan Broussard | Offline Score Library | Easiest | [`#/score-library`](http://localhost:5173/#/score-library) |

All four screen routes are implemented. The Score Viewer displays uploaded PDFs
and their detected measures with practice actions. Measure Marker and Practice
Review use the shared backend for the selected demo user's practice marks.

## Project structure

```text
frontend/                       React + Vite application
  src/App.jsx                   Hash routes and demo-user isolation
  src/OfflineScoreLibrary.jsx    Upload, reopen, and delete scores
  src/pages/ScoreViewer.jsx      Score navigation and practice actions
  src/pages/PdfScoreReader.jsx   Measure crops and full-page overlays
  src/PracticeReview.jsx         Saved passages, notes, and resolution
  src/components/score-companion/  Shared UI components and usage guide
backend/                        Django project
  config/                       Settings and root routing
  scoreapi/                     REST API, models, migrations, and tests
    upload_service.py           Deduplication and upload cleanup
    extraction_service.py       Extraction state and passage persistence
    score_extract.py            MusicXML and Audiveris layout import
    pdf_render.py               Original PDF page and measure images
  media/                        Local uploaded files (ignored by Git)
  requirements.txt              Backend dependencies
.local-tools/                   Optional local Audiveris install (ignored)
p9/                             Revised Figma PDF and P#9 instructions
p10/                            P#10 instructions and report
architecture.md                 Implemented architecture and limits
API_CONTRACT.md                 REST endpoints and data contract
```

## Local setup

### Prerequisites

- Python 3.12 or newer
- Node.js LTS
- Git
- Poppler and Audiveris for the PDF measure flow described above

Install Poppler through your system package manager (for example, `brew install
poppler` on macOS). Install Audiveris separately with a compatible Java runtime;
the local demo was verified with Audiveris 5.11 and its bundled Java runtime.
The application can discover its macOS installation automatically. For another
location, set the executable before starting Django:

```bash
export AUDIVERIS_COMMAND="/absolute/path/to/Audiveris"
```

### Backend

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py runserver
```

Migrations include the stored measure-coordinate schema. Existing installations
can also run `backend/.venv/bin/python backend/manage.py index_score_files` once
to fingerprint legacy uploads for deduplication; this does not merge or delete
existing scores. No sample scores are inserted during startup.

The API runs at `http://127.0.0.1:8000/`. Confirm it with:

```bash
curl http://127.0.0.1:8000/api/health/
```

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Vite serves the app at `http://localhost:5173/` and proxies `/api/` and `/media/`
to Django at `127.0.0.1:8000`. Keep both servers running.

For access from another device on the same network, start Django with
`backend/.venv/bin/python backend/manage.py runserver 0.0.0.0:8000` and Vite
with `npm run dev -- --host 0.0.0.0`. Open `http://<your-private-ip>:5173/`
on that device. This is a local development server with demo authentication.

### P#10 smoke test

With both servers and the PDF tools running:

1. Open `http://localhost:5173/#/score-library`, choose Alex Rivera, and upload
   a clear sheet-music PDF of at most 10 pages. Wait for recognition to finish.
2. Select different measure numbers. Confirm the music image changes and
   includes all staves, as well as showing the correct measure and page label.
3. Move to another page. Switch to **Full page**, select a highlighted measure
   region, and confirm its selected-measure preview loads.
4. Use **+ Practice**, open **Practice review**, confirm the saved measure, and
   resolve the mark.
   Use **Open passage** to return to the exact saved measure and page.
5. Switch to Sam Lee and confirm Alex's marks do not appear. Reuploading the
   identical PDF should reopen its existing library entry with its data intact.
6. With a disposable upload, use **Delete score** and confirm the library entry,
   original file, passages, and attached practice marks are removed.

### Score Viewer navigation

Open `http://localhost:5173/#/score-viewer`. To open a particular API score,
use `#/score-viewer?score=1` (replace `1` with its database ID). Library
integration can link to this route without changing the viewer.
Practice Review includes `&passage=<id>` to reopen the saved passage's page
within its original score.

The viewer requests the selected score and its passages through `/api/`; Vite
proxies these requests to Django at `127.0.0.1:8000`. Start both servers for
live data. An empty library asks you to add a score; it does not insert demo
content. Failed requests show a retry action and a return link to the library.

The original PDF provides the music notation. Audiveris supplies the measure
metadata and coordinates; Django renders each selected region from the original
PDF as a PNG. Full-page overlays use those same coordinates. Non-PDF metadata
previews use illustrative notation. OMR boundaries and numbering need visual
review against the source score.

Page, section, and measure jumps smoothly scroll and highlight the destination
measure so it remains easy to keep visual context while navigating a score.

### Verification status

The measure-image implementation is tracked in
[MR !26](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/merge_requests/26).
A Playwright browser check uploaded the real two-page PDF into an isolated
database, ran actual Audiveris recognition, clicked all 56 measures, and confirmed
that every image loaded. The resulting PNGs were distinct. Both full-page images
and their clickable regions also worked; selected crops were visually checked.

The same browser check saved and resolved a practice mark, reopened its exact
measure and page, verified demo-user isolation, reused an identical upload while
preserving practice data, and deleted the disposable score and source file.
There were no browser exceptions or failed application requests. Test database
and media storage were separate from the user's library.

All 30 backend tests, 17 frontend tests, and the production build pass. Lint
reports three existing Fast Refresh warnings in `mockSession.jsx`. Recognition
results still need review for each new score; the successful demo PDF does not
guarantee OMR accuracy on other files.

To repeat the automated checks:

```bash
backend/.venv/bin/python backend/manage.py test scoreapi
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
npm test --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
```

### Reusing frontend components

The viewer is composed from shared layout, heading, feedback, score context,
navigation, score sheet, measure preview, and measure-jump components.
See the [component usage guide](frontend/src/components/score-companion/README.md)
for props and examples for the other screen owners. Components accept data and
callbacks; each owner keeps their own API integration and screen behavior.

## API

The Django REST API is documented in [API_CONTRACT.md](API_CONTRACT.md).
The library upload flow creates scores and imports passages. Endpoints under
`/api/` provide scores, passage metadata, extraction state, practice marks, full
PDF page images, and individual measure previews.

## Development workflow

1. Work on a focused branch and use the assigned issue for context when available.
2. Use the revised Figma PDF as a reference alongside the implemented user flow.
3. Update affected API, README, and architecture documentation with the change.
4. Run relevant tests and verify the affected browser flow.
5. Open a GitLab merge request with validation results and issue links.
6. Merge verified work according to the agreed review process, then synchronize
   local `main` and the GitHub mirror with GitLab `main`.

## Prior project work

- [P#7 product overview and contributions](p7/P7-Team08/README.md)
- [P#7 report](p7/P7-Team08/P7-Team08-Report.pdf)
- [P#8 synthesis and implementation decisions](p8/P8_SYNTHESIS_AND_IMPLEMENTATION.md)
- [P#8 user-testing report](p8/P8_User_Testing_Report.pdf)
- [P#9 instructions](p9/instruction.md)
- [P#10 instructions](p10/instruction.md)

## License

See [LICENSE](LICENSE). The license covers only Ankit Joshi's original contributions. Team work, research records, participant material, and course-provided documents are excluded unless separately licensed.
