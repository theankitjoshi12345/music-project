# Score Companion

Score Companion is a CMPS 453 team project for helping musicians open downloaded score parts, mark passages for practice, add a practice note, and review unresolved corrections.

## P#9 status

The shared REST API and all four assigned screens are present in `main`: Logan's Offline Score Library, Ankit's Score Viewer & Navigation, Matthew's Measure Marker, and Jonathan's Practice Review. The revised Figma PDF is the primary UI reference.

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

All four screen routes are implemented. The Score Viewer supports page controls, section selection, and jumping to a measure. The Measure Marker uses local demo data and browser storage; its marks are not yet shared with the backend or Practice Review. See [Measure Marker notes](p9/MEASURE_MARKER.md) for its scope. Practice Review reads and resolves backend practice marks.

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

### Score Viewer (#24)

Open `http://localhost:5173/#/score-viewer`. To open a particular API score,
use `#/score-viewer?score=1` (replace `1` with its database ID). Library
integration can link to this route without changing the viewer.

The viewer requests the selected score and its passages through `/api/`; Vite
proxies these requests to Django at `127.0.0.1:8000`. Start both servers for
live data. An empty library displays a clearly labeled sample reproducing
Section B, measures 17–24 from page 2 of the revised PDF. Failed requests show
a retry action and an explicit option to view the sample.

Notation is illustrative: the current API provides measure metadata, not music
notation or score-file contents. PDF rendering, actual offline file caching,
and measure-marking actions are outside this screen's implementation. The
viewer does not claim a score is offline-ready.

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
