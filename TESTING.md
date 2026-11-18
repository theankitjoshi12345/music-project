# Testing Score Companion

Score Companion uses three complementary checks: Django unit/integration tests
for backend rules, Node tests for frontend logic and rendered components, and a
Playwright golden-path test against an isolated running application. P12 keeps
the fast tests deterministic and uses MusicXML for the browser path so the test
does not depend on Audiveris or production data.

## Prerequisites

- Python 3.12 and a virtual environment with `backend/requirements-docker.txt`.
- Node.js 22 and `npm ci` in `frontend/`.
- Chromium for the E2E command. Install it once with
  `cd frontend && npx playwright install chromium`.

Create a development secret before Django commands:

```bash
export DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')"
```

## Fast local checks

```bash
backend/.venv/bin/pip install -r backend/requirements-docker.txt
backend/.venv/bin/coverage run backend/manage.py test scoreapi --verbosity 1
backend/.venv/bin/coverage report
backend/.venv/bin/coverage html

cd frontend
npm ci
npm run lint
npm test
npm run test:coverage
npm run build
```

Backend coverage is branch-aware and measures production `backend/scoreapi`
code. Migrations, management commands, and test modules are excluded because
they are framework scaffolding or test code rather than application behavior.
The enforced floor is 80%. Frontend coverage targets the deterministic core
data and request modules (`scoreViewerData`, `extractionRequest`,
`extractionTiming`, and `measureNavigation`) at 80% lines/statements/functions
and 70% branches. JSX screen composition is additionally exercised by the
server-rendered component tests and the real-browser test.

Coverage reports are generated at `coverage/backend-html/index.html` and
`frontend/coverage/index.html`; GitLab retains the corresponding Cobertura XML
and HTML artifacts for 30 days.

## Golden-path E2E

Use an isolated temporary data directory. This command starts Django in explicit
`demo` mode only for test data, runs Vite, then drives the actual UI. It uploads
a generated MusicXML fixture, opens a measure, saves it for practice, marks it
practiced in Practice Review, returns to the measure, and removes the score.

Terminal 1:

```bash
mkdir -p /tmp/score-companion-p12-e2e
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
  DJANGO_AUTH_MODE=demo \
  DJANGO_DATA_DIR=/tmp/score-companion-p12-e2e \
  backend/.venv/bin/python backend/manage.py migrate --noinput
DJANGO_SECRET_KEY="$DJANGO_SECRET_KEY" \
  DJANGO_AUTH_MODE=demo \
  DJANGO_DATA_DIR=/tmp/score-companion-p12-e2e \
  backend/.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

Terminal 2:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Terminal 3:

```bash
cd frontend
E2E_ORIGIN=http://127.0.0.1:5173 npm run test:e2e:golden
```

The longer `npm run test:e2e` suite remains available for PDF/OMR coverage and
requires an isolated PDF fixture plus the full local Audiveris stack. It is not
the P12 CI gate because its native recognition dependency is intentionally
outside the reliable browser regression path. Never point E2E tests at another
person's library or the public production data store.

## CI mapping

| GitLab job | Local equivalent | Trigger |
| --- | --- | --- |
| `backend-tests` | `coverage run backend/manage.py test scoreapi`, then `coverage report/html/xml` | Merge requests and branch pushes |
| `frontend-tests` | `npm run lint && npm test && npm run test:coverage && npm run build` | Merge requests and branch pushes |
| `e2e-golden-path` | Start isolated demo Django + Vite, then `npm run test:e2e:golden` | Merge requests and branch pushes |
| `firestore-integration` | `python backend/manage.py smoke_firestore` with the emulator variables | Merge requests and branch pushes |

Deployment remains protected-main-only; P12 test jobs run before package and
deployment stages. A failed test or coverage threshold fails its job.

## Troubleshooting

**The browser test cannot reach `/api/session/`.** Verify Django is running on
port 8000, Vite is running on port 5173, and start Vite with the exact
`--host 127.0.0.1 --port 5173 --strictPort` flags above. The Vite proxy sends
`/api` to Django. If a stale temporary test run has data, choose a new empty
`DJANGO_DATA_DIR`; the E2E test cleans up its own score but does not delete an
unrelated test directory.
