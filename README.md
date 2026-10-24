# Score Companion

Score Companion is a CMPS 453 team project for helping musicians open downloaded score parts, mark passages for practice, add a practice note, and review unresolved corrections.

## P#9 status

The Django + React application shell is initialized. It provides a verified API health endpoint and four owner-reserved frontend routes. The revised Figma screens are the primary UI reference, but their designs have intentionally **not** been implemented in this setup commit. Each owner builds only their assigned screen in a separate issue and branch.

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

These routes are placeholders only. Do not implement another member's screen.

## Project structure

```text
frontend/                 React + Vite application
  src/App.jsx             Shared app shell and placeholder hash routes
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
