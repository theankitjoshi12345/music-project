# Score Companion

Score Companion is a CMPS 453 team project for helping musicians open downloaded score parts, mark passages for practice, add a practice note, and review unresolved corrections.

## P#10 local MVP

The shared REST API and all four assigned screens are present in `main`: Logan's Offline Score Library, Ankit's Score Viewer & Navigation, Matthew's Measure Marker, and Jonathan's Practice Review. The P#10 golden path is: open the downloaded score in the library, view the selected score, mark a measure for practice, then review or resolve that measure and return to its score context.

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

### Optional local PDF measure extraction

Install Poppler (`pdftoppm` and `pdfinfo`) and Audiveris. Set `AUDIVERIS_COMMAND`
to the executable, or install it on PATH. On macOS the app also checks
`/Applications/Audiveris.app` and `.local-tools/Audiveris.app` in this checkout.
The mounted installer is not used as the runtime. The binary is local-only and
excluded from Git; a new deployment must install it separately.

The demo limits recognition to PDFs with at most 10 pages and bounds rendering
and recognition time. A second request for the same score shares the processing
state; completed imports are reused. Failed/repeated extraction preserves
existing measures and practice notes. Audiveris is licensed under AGPL-3.0;
upstream source and license: https://github.com/Audiveris/audiveris.

## Tech stack

| Area | Choice |
| --- | --- |
| Frontend | React + Vite (JavaScript) |
| Backend | Django + Django REST Framework |
| Database | SQLite |
| Runtime | Python 3.12+ and Node.js LTS |
| IDE | VS Code |
| Version control | Git + GitLab |
| API testing | Postman (recommended) |
| UI reference | [Score Companion Figma design](https://www.figma.com/design/NSZliKsVC3CiwrjqQfrOHS) and export: `p9/Score_Companion_P8_Revised_Screens.pdf` |

See [architecture.md](architecture.md) for the planned architecture and boundaries.

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
frontend/                 React + Vite application
  src/App.jsx             Shared app shell and placeholder hash routes
  src/pages/ScoreViewer.jsx  Ankit's Score Viewer & Navigation
  src/components/score-companion/  Shared UI components and teammate usage guide
backend/                  Django project
  config/                 Django settings and root routing
  scoreapi/               Initial REST API app
  requirements.txt        Backend dependencies
p9/                       P#9 instructions and revised Figma PDF reference
architecture.md           Planned technical architecture
API_CONTRACT.md           Shared REST endpoint and data contract
```

## Local setup

### Prerequisites

- Python 3.12 or newer
- Node.js LTS
- Git

### Backend

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py index_score_files
backend/.venv/bin/python backend/manage.py runserver
```

The API runs at `http://127.0.0.1:8000/`. Confirm it with:

```bash
curl http://127.0.0.1:8000/api/health/
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves the app at `http://localhost:5173/`. Use the navigation links to visit each reserved route.

### P#10 smoke test

With both servers running, open `http://localhost:5173/#/score-library` on the
`main` branch. Optionally upload a score, choose Alex Rivera, open the available
score, visit Measure Marker, select a measure, use the persistent **Save measure**
action, and open Practice Review. Resolve the mark and use
**Open passage** to return to the correct score context. Switch to Sam Lee to
confirm that Alex's practice mark does not appear for the other mock user.

### Score Viewer (#24)

Open `http://localhost:5173/#/score-viewer`. To open a particular API score,
use `#/score-viewer?score=1` (replace `1` with its database ID). Library
integration can link to this route without changing the viewer.
Practice Review includes `&passage=<id>` to reopen the saved passage's page
within its original score.

The viewer requests the selected score and its passages through `/api/`; Vite
proxies these requests to Django at `127.0.0.1:8000`. Start both servers for
live data. An empty library asks you to add a score; it does not insert demo
content. Failed requests show a retry action and a return link to the library.

The original PDF provides the music notation. OMR supplies a detected measure
list for navigation and saving practice marks. Actual offline caching is not
implemented. Non-PDF metadata previews use illustrative notation.

Page, section, and measure jumps smoothly scroll and highlight the destination
measure so it remains easy to keep visual context while navigating a score.

Run `npm test --prefix frontend`, `npm run lint --prefix frontend`, and
`npm run build --prefix frontend` to verify the viewer's data integration and build.

### Reusing frontend components

The viewer is composed from shared layout, heading, feedback, score context,
navigation, score sheet, measure preview, and measure-jump components.
See the [component usage guide](frontend/src/components/score-companion/README.md)
for props and examples for the other screen owners. Components accept data and
callbacks; each owner keeps their own API integration and screen behavior.

## API

The Django REST API is documented in [API_CONTRACT.md](API_CONTRACT.md).
After creating data through the Django admin, shell, or fixtures, the primary
endpoints are scores, score passages, and practice marks under `/api/`.

Run backend API tests with:

```bash
backend/.venv/bin/python backend/manage.py test scoreapi
```

## Development workflow

1. Read the revised Figma PDF before building a screen.
2. Work only on your assigned GitLab issue and branch.
3. Build your owned screen; do not modify another owner's screen without coordination.
4. Test the frontend and relevant API requests.
5. Open a GitLab merge request with `Closes #<issue-number>`.
6. Request teammate review before merging.

## Prior project work

- [P#7 product overview and contributions](p7/P7-Team08/README.md)
- [P#7 report](p7/P7-Team08/P7-Team08-Report.pdf)
- [P#8 synthesis and implementation decisions](p8/P8_SYNTHESIS_AND_IMPLEMENTATION.md)
- [P#8 user-testing report](p8/P8_User_Testing_Report.pdf)
- [P#9 instructions](p9/instruction.md)

## License

See [LICENSE](LICENSE). The license covers only Ankit Joshi's original contributions. Team work, research records, participant material, and course-provided documents are excluded unless separately licensed.
