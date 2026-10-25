# Architecture — Score Companion

**Status:** P#9 app shell is implemented. The project currently includes a shared React shell, a Django health endpoint, and the planned screen-route structure for future feature work.
**Status:** Planned architecture for P#9. The shared API contract is implemented
on feature branch `28-shared-api-contract` and awaits team review; no screen
implementation is included in that work.

Score Companion is intended to support musicians opening score parts, marking passages for practice, adding contextual notes, and reviewing unresolved passages.

## System Overview

```text
React + Vite client
        │ HTTPS / JSON
        ▼
Django REST Framework API
        │ Django ORM
        ▼
SQLite database
```

The React client will provide the user interface. Django REST Framework will expose application data through a JSON API. Django will use its ORM to persist data in SQLite during development.

## Technology Decisions

| Area | Planned choice | Classification | Purpose |
| --- | --- | --- | --- |
| Frontend | React + Vite (JavaScript) | **Mandatory** | Build the browser-based user interface. |
| Backend | Django + Django REST Framework | **Mandatory** | Provide server-side application logic and REST API endpoints. |
| Database | SQLite | **Mandatory** | Persist development data through Django's ORM. |
| Runtime | Python 3 + Node.js LTS | **Mandatory** | Run the Django backend and React/Vite frontend. |
| Version control and hosting | Git + GitLab | **Mandatory** | Track source changes and support the P#9 issue and merge-request workflow. |
| Project tracking | GitLab | **Mandatory** | Source of truth for milestones, issues, branches, merge requests, and reviews. |
| IDE | VS Code | **Recommended** | Shared development environment for the team. |
| AI assistant | Codex or GitHub Copilot | **Recommended** | Assist with setup, implementation, and debugging. |
| API testing | Postman | **Recommended** | Send and inspect requests to the REST API during development. |
| UI design | Figma | **Recommended** | Maintain the approved screen designs and guide implementation. |

## Planned Repository Layout

```text
music-project/
├── frontend/                 # React + Vite application
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Route-level screens
│   │   ├── services/         # API client functions
│   │   └── styles/           # Application styles
│   └── package.json
├── backend/                  # Django project
│   ├── config/               # Django settings and root URL routing
│   ├── scores/               # Score, mark, note, and review domain app
│   ├── manage.py
│   └── requirements.txt
├── architecture.md           # This planned architecture
└── README.md                 # Setup and project overview
```

The exact Django app names and React component structure may evolve during implementation, but the frontend/backend separation is planned.

## Planned Responsibilities

### Frontend — React + Vite

The client will implement the Figma-informed screens and user flow:

1. Offline score library.
2. Score viewer with piece, movement, and measure context.
3. **Mark for practice** action for selected measures.
4. Practice-note entry for marked passages.
5. Unresolved-passage review and resolved confirmation.

The frontend will call the backend API and present loading, success, and error feedback.

### Backend — Django + Django REST Framework

The backend will:

- Define models and validation rules.
- Provide JSON endpoints for score data, practice marks, notes, and review status.
- Use Django migrations to manage the SQLite schema.
- Return clear validation and error responses to the frontend.

### Database — SQLite

SQLite is planned for local development. It will store the application's data through Django models. Any future production database decision is outside the P#9 scope.

## Planned API Boundaries

The exact endpoint paths are not final. The initial REST resources are planned as follows:

| Resource | Planned responsibility |
| --- | --- |
| Scores | List available score parts and retrieve score context. |
| Passages | Retrieve passages or measures associated with a score. |
| Practice marks | Create, list, and update a marked passage. |
| Practice notes | Attach contextual notes to a marked passage. |
| Review items | List unresolved passages and mark an item resolved. |

## Development Workflow

1. Use Figma as the visual reference for each assigned screen.
2. Create and assign work through GitLab issues.
3. Create a Git branch from the assigned issue.
4. Implement one owned screen or scoped feature at a time.
5. Test API requests with Postman when useful.
6. Open a GitLab merge request that includes `Closes #<issue-number>`.
7. Obtain a teammate review, merge the change, and verify that the linked issue closes.

> GitLab is the project's authoritative tracker. GitHub may mirror repository files, but it must not be used for issues, milestones, or pull-request workflow for this project.

## Local Development Prerequisites

### Mandatory

- Python 3
- Node.js LTS
- Git
- Access to the team GitLab project

### Recommended

- VS Code
- Codex or GitHub Copilot
- Postman
- Access to the team's Figma design file

## Planned Local Startup

These commands describe the intended layout once the application skeleton is created.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend development server will call the local Django API. Exact ports, environment variables, and CORS configuration will be added when the skeleton is created.

## Out of Scope for This Planned Architecture

- Production hosting and deployment.
- A production database migration.
- Authentication and account management.
- Online score browsing, social features, tuner/metronome tools, or automatic error detection.
- Claims of implemented offline storage, PDF handling, or saved annotations before those features are built.
