# P10 Integrated MVP Local Report

## Scope and golden path

Score Companion is a local React and Django application for a musician who
needs to locate a downloaded score, flag a difficult measure, and return to it
during practice review. The tested P10 journey starts in the Offline Score
Library, opens a selected score in Score Viewer, marks a measure in Measure
Marker, then opens Practice Review to resolve the mark or return to the exact
score passage.

The app uses a local mock-user selector rather than production authentication.
Alex Rivera and Sam Lee see separate practice-mark records. The selected user
is sent to the local API in the `X-Mock-User` request header; this is only a
development placeholder.

## Data and integration contract

The source of truth is [API_CONTRACT.md](../API_CONTRACT.md). The path uses
four shared entities:

| Entity | Golden-path responsibility |
| --- | --- |
| User | Owns locally scoped practice marks through the mock-user ID. |
| Score | Starts the path in the offline library and identifies the viewer context. |
| Passage | Carries the score, section, measure, and page used by marker and review. |
| PracticeMark | Connects a user to one passage, with resolution state and an optional note. |

Integration handoffs are: Library passes `score` to Viewer; Marker reads that
score's passages and creates a `PracticeMark`; Practice Review filters the
active user's marks, resolves a mark, and links to the original score and
passage.

## Completed implementation evidence

| GitLab issue | Merge request | Outcome |
| --- | --- | --- |
| #30 Shared mock user and golden path integration | !8 | Added shared mock-user state, user-scoped API marks, migration, and API-contract updates. |
| #31 Library to viewer handoff | !9 | Replaced static library cards with API data and exact viewer links. |
| #32 Marker to review handoff | !10 | Replaced browser-only marker state with API-backed practice-mark creation. |
| #33 Practice review completion loop | !11 | Scoped review and resolve actions to the selected demo user. |
| #34 Integration smoke test README and report evidence | This change set | Added local demo data, README run and smoke-test steps, and this evidence record. |

The issue assignments record the intended team slices. This record does not
claim that the listed assignees authored work they did not submit; GitLab merge
request history is the authoritative contribution evidence.

## Local run and smoke test

From a clean checkout of `main`:

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py loaddata demo_scores
backend/.venv/bin/python backend/manage.py runserver

cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/#/score-library`. Choose Alex Rivera, open the
available score, navigate to Measure Marker, save a measure, and open Practice
Review. Resolve that mark and use **Open passage** to return to the selected
score. Switch to Sam Lee to verify that Alex's mark is not shown.

## Automated verification

The following checks pass on the integration branch:

```bash
backend/.venv/bin/python backend/manage.py test scoreapi
npm test --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
```

The backend suite includes coverage for two mock users creating independent
marks for the same passage. The frontend suite checks routing and score/passage
link construction. Lint completes with Fast Refresh advisory warnings for the
shared session module; it reports no lint errors.

## Demo and screenshot checklist

Use a 60–90 second local demo: select Alex, open a score, save one measure,
resolve it in review, return to the passage, then switch to Sam to show the
user-scoped empty state. Capture screenshots only after the final merged
`main` smoke test so they show the same route, user, and data as the demo.

## AI usage

AI assistance was used to organize the P10 plan, draft implementation changes,
and identify API integration gaps. The implementation was validated with the
repository's automated tests and production build. A correction made during
development was replacing an automatic Django uniqueness error with the
project's intended `passage_id` validation response, then adding a two-user
isolation test.

## Remaining submission evidence

- Run and record one clean-clone check from the final GitLab `main` branch.
- Capture the golden-path screenshots and add them to the supplied Word report
  template if that template is the required submission format.
- Add only verified reviewer and teammate contribution details to the final
  course submission.
