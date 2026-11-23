# P12 Unit and End to End Testing

**Course:** CMPS453  
**Product:** Score Companion  
**Team:** 08  
**Due:** Sunday, November 29, 2026, 11:55 PM

## Purpose

P12 extends the completed P11 launch with repeatable automated quality checks:
meaningful unit and integration tests, an end-to-end test of the P10 golden
path, and CI jobs that run those checks for merge requests and pushes. The
assignment is evaluated on fast feedback, reproducibility, and evidence kept in
the repository.

Score Companion is a browser-based web application. The web-application
requirements below apply. The Moodle assignment is authoritative; the included
web QA guide is implementation guidance only.

## Required deliverables

| Deliverable | What it must demonstrate |
| --- | --- |
| Automated unit and integration tests | Meaningful coverage of non-trivial application logic and components. |
| Automated E2E test | At least one golden-path spec against a running local or CI build. |
| CI configuration | Lint (if used), unit tests, E2E, and build run for merge requests or equivalent pushes. |
| `TESTING.md` | Local commands, prerequisites, CI mapping, and one common troubleshooting path. |
| Root `README.md` testing section | Copy-paste test commands plus links to CI jobs and coverage artifacts. |
| `TEST-RESULTS.md` or CI summary | Approximate test counts, coverage results, exclusions, and last green pipeline evidence. |
| P12 report | Completed from `P12-Report-template.docx`, including work performed, metrics, and the P12 team schedule. |

## Web application expectations

### Unit and integration testing

- Test non-trivial logic, not just smoke rendering. Suitable targets include
  validation, services, reducers, API clients with mocks, and React components.
- Use framework-appropriate tools. For this project, the existing JavaScript,
  React, Django, and browser-testing stack should be extended rather than
  replaced without reason.
- Set defensible line and branch coverage thresholds for application code,
  excluding generated files and configuration. The guide's typical starting
  target is at least 80% lines and 70% branches for `src/`; explain and record
  any lower threshold or exclusion.
- Store coverage HTML or a CI artifact and document its location.

### End-to-end testing

- Maintain at least one automated E2E specification for the P10 golden path
  against a running build.
- For Score Companion, the golden path is: authenticate; upload a permitted PDF
  or MusicXML score; wait for conversion; open a measure; save an optional
  practice note; open Practice Review; mark it practiced; return to the score;
  and remove test data.
- Playwright or Cypress are typical tools. Existing Playwright coverage may be
  extended and must remain deterministic, isolated, and cleanup its own data.
- A second regression/failure spec is recommended, especially for an auth wall,
  empty state, throttled conversion, or user-isolation boundary.

### CI policy

- Run lint (if used), unit/integration tests, E2E tests, and the production
  build in GitLab CI or GitHub Actions for merge requests and/or comparable
  pushes.
- Prefer a green E2E job. An `allow_failure` E2E job is only acceptable when
  the rationale is documented and it still runs on `main`.
- Do not merge with an agreement to fix tests later unless the instructor has
  explicitly approved it.
- Preserve P11 deployment and security jobs while adding P12 quality evidence.

## Documentation to add

### `TESTING.md`

Include all of the following:

1. Required local tools and setup.
2. Exact copy-paste commands for backend tests, frontend unit tests, coverage,
   E2E, and any service startup required by E2E.
3. A CI-to-local mapping table that names the CI job, the corresponding command,
   and its trigger.
4. Test-data isolation and cleanup behavior for E2E.
5. One common failure and its troubleshooting steps.

### Root `README.md`

Add a concise **Testing** section with copy-paste commands and links to the
pipeline jobs and coverage artifact or path. Link to the canonical `TESTING.md`.

### `TEST-RESULTS.md`

Record the current approximate test counts, coverage percentages, threshold and
exclusion rationale, E2E scenarios, and a link to the most recent green
pipeline. Keep claims factual and update this file when the suite changes.

## Suggested implementation sequence

1. Inspect the existing backend, frontend, Playwright, and CI suites; identify
   untested non-trivial logic and the current E2E golden path.
2. Define coverage scope, thresholds, and exclusions that the team can defend.
3. Add or improve focused unit and integration tests.
4. Make the golden-path E2E test reliable in an isolated environment; add one
   useful regression test if feasible.
5. Wire every command into CI and retain test/coverage artifacts.
6. Write `TESTING.md`, update the README, and record current evidence in
   `TEST-RESULTS.md`.
7. Complete the official P12 report template and export/inspect the PDF before
   submission.

## Evaluation rubric

| Criterion | Weight | Strong evidence |
| --- | ---: | --- |
| Unit tests | 30% | Meaningful, stable tests targeting real logic and components in CI. |
| E2E and user path | 30% | Automated P10 golden path; additional regression coverage where useful. |
| CI integration | 25% | Clear pipeline that fails when tests fail; documented E2E policy. |
| Documentation | 15% | Reproducible `TESTING.md`, clear README commands, and honest results. |

## Reference files

- `P12-WebApp-QA-Guide.docx` — implementation guidance for the web stack.
- `P12-Report-template.docx` — required report template.
- `P12-grader-notes.docx` — supporting grading guidance.

The desktop and mobile guides from Moodle do not apply to Score Companion, but
the general expectations for automation, CI, documentation, and honest evidence
remain the same.
