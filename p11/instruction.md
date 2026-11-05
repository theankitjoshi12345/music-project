# P11 Launch instructions

**Course:** CMPS453  
**Product:** Score Companion  
**Team:** 08  
**Deadline:** November 9, 2026

Launch the existing P10 product at a verified public HTTPS URL. A new user must
be able to upload sheet music, extract and view measures, save a practice note,
and return to that passage. Complete repeatable GitLab delivery, document the
actual security controls, and submit the official report as Word and PDF.

## Sources and grading

The supplied [report template](P11-Report-template.docx) defines the report
sections. The supplied [grader notes](P11-grader-notes.docx) define these weights:

| Criterion | Weight | Required evidence |
| --- | ---: | --- |
| Launch and accessibility | 30% | Stable public access, a working core task, appropriate hosting, and an outside tester when possible. |
| User-facing documentation | 25% | A stranger can get the product and complete the core task from the README; production configuration is explained. |
| CI/CD for launch | 20% | Meaningful build/test jobs and a repeatable deploy or artifact path, with secrets held outside source. |
| Security configuration | 20% | Specific application and infrastructure controls, with limitations stated honestly. |
| Professional polish | 5% | A clear PDF, working links, and screenshots from the real launch. |

P11 covers launch, documentation, CI/CD, and security. The final presentation and
live demo belong to P13. No demo video is part of this submission.

## Preserve the project and previous work

- Keep application code, deployment configuration, CI, tests, and operational
  scripts in the project root or existing application directories.
- Update root `README.md` and lowercase `architecture.md`; do not create copies
  of those permanent project guides under this directory.
- Put assignment instructions, reports, grading checklists, contributions, and
  launch evidence under `p11/`.
- Preserve `p10/` and earlier assignments. Reuse the integrated P10 golden path.
- Preserve existing user PDFs and practice data. Do not seed dummy content into
  a user's real library or publish private local files.

## Inspect and choose hosting

Inspect the actual code, Git history/remotes, data model, native dependencies,
and current cloud state before choosing a host. The application includes Django,
React/Vite, SQLite, uploaded files, Poppler, and Audiveris; it is not stateless.

Prefer Google Cloud when technically and financially suitable. Do not force
Firestore onto Django's relational ORM. Use a compatible persistent database and
durable file storage. Verify free-tier conditions before provisioning; approval
is required before billing or resources that may incur charges.

The architecture must support x86_64 Audiveris, Java, Poppler, bounded PDF
recognition, and cleanup. Data must survive backend restarts, container
replacement, redeployment, and scale-down. Never use ephemeral container files
as the only copy of uploads or database records. Do not remove recognition to
make hosting easier.

## Prepare and verify the application

1. Configure production Django hosts, DEBUG, CSRF, authentication, authorization,
   cookies, static files, persistent storage, logging, health checks, and safe
   migrations. Protect admin and uploaded files.
2. Build React for the deployed API and HTTPS routing. No production request may
   depend on a developer's localhost. Keep existing screens and navigation.
3. Isolate each visitor's PDFs and practice records. Development profile headers
   are not production authentication.
4. Preserve native and one-command Docker startup. Run backend/frontend tests,
   lint, production build, dependency checks, and Django deployment checks.
5. Verify the real public frontend, assets, API, upload, recognition, measure
   display, note creation/retrieval, and cleanup in a fresh browser context.
6. Verify persistence across a restart or redeployment and record the exact
   deployed commit, URL, environment, and observed result.

## Deliver through GitLab

Use feature branches and merge requests without bypassing protections. Configure
root `.gitlab-ci.yml` with backend checks/tests, frontend checks/tests/build,
dependency vulnerability checks, deployment after required checks, and a
post-deployment health check. Prefer short-lived deployment identity; otherwise
use appropriately protected CI variables. Never commit credentials or expose
them in the frontend. Keep GitHub consistent with the authoritative GitLab
repository. A merged MR alone is not a completed public launch.

## Maintain permanent documentation

Root README must distinguish local development, Docker startup, cloud deployment,
and the user guide. Include actual commands, environment settings, limitations,
and the verified public link.

Root architecture must describe local, Docker, production, and CI/CD flows with
Mermaid diagrams that match the implementation. Explain database/file persistence,
recognition, authentication, networking, secrets, logging, and recovery decisions.

## Complete the assignment evidence

Use the official report template and include the public URL, platform and
decision, real launch screenshots, challenges and resolutions, user guide link,
pipeline evidence, application/infrastructure security, delivery schedule, launch
checklist, and remaining limitations. Export the Word report to PDF and inspect
every page. Keep source material beside the report.

Record contributions from actual work and repository history. A real non-team
person must try the deployed core task; an automated or simulated user does not
satisfy that requirement. Record the date, task, result, and any issue without
inventing observations. Mark missing evidence pending.

## Completion rule

The launch is complete only when the real HTTPS application and core workflow
are verified, CI/CD is reproducible, docs match reality, and P11 evidence is
organized here. Continue safe independent work through ordinary errors. If an
account, billing approval, permission, protected branch, or actual outside tester
is required, identify the exact remaining human action and do not claim success.
