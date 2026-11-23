# P12 Test Results

**Recorded:** November 18, 2026  
**Product:** Score Companion · Team 08

## Current local verification

| Check | Result | Evidence |
| --- | --- | --- |
| Django unit and integration suite | 79 passing tests | `backend/manage.py test scoreapi` |
| Backend coverage | 87% branch-aware production-code coverage | `coverage report`; 80% enforced floor |
| Frontend unit and component suite | 27 passing tests | `npm test` |
| Frontend core-logic coverage | 100% lines; 96.67% branches; 90% functions | `npm run test:coverage`; 80/70 enforced floors |
| Browser golden path | Passing | `E2E_ORIGIN=http://127.0.0.1:5173 npm run test:e2e:golden` |

## Covered behavior

- Backend: authentication and account isolation, uploads and quotas, persistent
  recognition allowance, private storage/file access, extraction safety,
  serializer validation, practice records, deletion, and Firestore smoke
  integration.
- Frontend: score selection, page/measure navigation, conversion timing,
  extraction ticket error/retry behavior, component rendering, loading/error
  states, and accessibility labels.
- E2E: isolated MusicXML upload, score/measure selection, practice save,
  Practice Review completion, return to the measure, and cleanup.

## Coverage scope and exclusions

Backend coverage excludes migrations, management commands, and test modules.
Frontend threshold coverage is scoped to deterministic data/request modules;
screen composition is covered by component rendering tests and the browser
golden path. Audiveris/PDF recognition remains covered by backend tests and the
optional longer local workflow, but is not a shared-runner E2E dependency.

## CI evidence

Verified green P12 merge-request pipeline:
[3086384025](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3086384025)
(MR !53, commit `1c1dfb5`). Its P12 test jobs all passed:

- [`backend-tests`](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/jobs/18162365965)
  ran Django checks, migrations, 79 tests, and branch coverage. Its retained
  artifacts contain `coverage/backend-html/index.html` and
  `coverage/backend.xml` (Cobertura).
- [`frontend-tests`](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/jobs/18162365968)
  ran lint, 27 unit/component tests, enforced frontend coverage, and the
  production build. Frontend coverage is printed in this job's log.
- [`e2e-golden-path`](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/jobs/18162365969)
  passed the isolated Playwright upload → measure → practice-review → cleanup
  workflow.

The coverage and job artifacts for this pipeline expire after 30 days, on
December 18, 2026. GitLab project settings currently do not require a passing
pipeline before a merge; this evidence records the verified green pipeline
used for the P12 review rather than claiming an enforced protection.
