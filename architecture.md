# Score Companion architecture

This describes the implemented local system and live Google Cloud deployment
at `https://music-companion-513717.web.app`. CI verifies the exact public
frontend, health endpoint, and session configuration after every enabled
protected-main deployment.

## Runtime boundaries

```text
Browser
  ├─ Google Identity Services → Google ID token
  └─ Firebase Hosting → React/Vite assets
       ├─ /api/** rewrite → Cloud Run Django API (short requests)
       └─ signed OMR ticket → Cloud Run directly (long request only)
                                  ├─ Poppler → PDF pages/crops
                                  ├─ Audiveris → MusicXML + measure geometry
                                  ├─ Firestore Datastore mode → metadata
                                  ├─ private GCS → PDFs + PNG cache
                                  └─ Secret Manager → signing key
```

Local Docker substitutes Nginx, SQLite, filesystem media, and a named volume.
Native development runs Vite and Django separately. Neither path writes to
cloud persistence.

## Identity and request security

Production uses `DJANGO_AUTH_MODE=google`:

1. Google Identity Services returns an ID token.
2. `/api/auth/google/` enforces CSRF and verifies the token audience.
3. `sub` must exist and `email_verified` must be true.
4. Ownership is `SHA-256(sub)`; email is display-only.
5. Identity state uses an HTTP-only, Secure, SameSite=Lax signed cookie.
6. Score queries begin with owner; child routes verify through the score.

Normal API traffic is same-origin through Firebase. Its 60-second serverless
rewrite timeout is too short for Audiveris, so an authenticated endpoint signs
`{owner, score_id}` with a dedicated salt. Only the direct extraction route
accepts that bearer ticket, for at most 15 minutes. Altered/wrong-score tickets
fail, and CORS allows only the project's `.web.app` and `.firebaseapp.com`
origins.

Hosting strips ordinary cookies before a rewritten request and permits only
`__session`. The production Django session deliberately uses that name, plus
Secure, HTTP-only, SameSite=Lax attributes, so the signed Google identity
reaches Cloud Run and participates in Firebase's per-session cache key.

GCS uses uniform access and public-access prevention. Django returns original
and derived files only after ownership checks. Production disables Django admin
and database-backed user tables.

## Data model

| Record | Main fields | Constraint |
| --- | --- | --- |
| `Score` | owner, metadata, source path/bytes/SHA, counts, extraction state/layout | owner + content SHA |
| `Passage` | score, section, measure, page, normalized box | score + section + measure |
| `PracticeMark` | owner, passage, note, resolved state, timestamps | passage + owner |

Django uses SQLite locally and Firestore in Datastore mode publicly through
`django-gcloud-connectors`. Cloud queries avoid joins, aggregate annotations,
and composite ordering. Bounded results are sorted in Python. Emulator tests
cover migrations and the full two-account API lifecycle.

`backend/index.yaml` defines the one composite production lookup: score owner
plus content SHA for idempotent duplicate uploads. CI creates it with the
short-lived deploy identity and blocks release until Datastore reports the
index ready; the query explicitly clears display ordering so no wider index is
required.

## Conflict-safe objects and deletion

Uploads are SHA-256 addressed as
`scores/<owner>/<sha256>.<extension>`. GCS writes use
`if_generation_match=0` and CRC32C so concurrent identical uploads converge.
Database uniqueness preserves the first completed record. Failed writes remove
only unreferenced objects.

Generated cache keys include owner, source digest, and layout version. Cloud
objects are materialized in a private temporary directory only while Poppler or
Audiveris needs them. Generation-guarded deletion prevents a stale request from
deleting a replacement. Score cleanup is child-first: marks, passages, derived
prefix, source object, then score.

## PDF recognition

1. `pdfinfo` validates at most 10 pages.
2. `pdftoppm` renders 300-dpi recognition pages ephemerally.
3. Audiveris 5.11 transcribes/exports MusicXML and `.omr` geometry.
4. Measure identities and normalized bounding boxes become passages.
5. Retries update section/measure keys, preserving IDs and practice marks.
6. Completion is published only after every measure is stored.

A file lock permits one Audiveris process; Cloud Run also has one instance and
concurrency four with four Gunicorn threads, leaving capacity for library and
session requests during recognition. A stale processing lease becomes retryable
after the deadline plus 90 seconds. The UI polls every five seconds and skips
a poll while its previous request is pending.
Display uses 150-dpi full pages and 300-dpi crops from the original PDF.

## Deployable artifacts

The `cloudrun` image contains Ubuntu 24.04 amd64, Django/Gunicorn, Poppler, and
checksum-verified Audiveris with Java/native dependencies. It runs as UID 10001
and contains no frontend assets. Cloud Run uses request billing, 1 vCPU, 4 GiB,
15-minute timeout, min 0, max 1, concurrency 4, and no startup CPU boost.

Firebase deploys `frontend/dist`, caches hashed assets immutably, does not cache
`index.html`, rewrites `/api/**` to `music-companion-api` in `us-central1`, and
falls back to `index.html` for SPA routes.

## Cost controls and residual risk

| Resource | Guard |
| --- | --- |
| Cloud Run | min 0, max 1, concurrency 4; one OMR lock |
| Requests | 10,000/account-or-IP/hour |
| Uploads | 100/account/day; 10 MB/file |
| Recognition | 20/account/day; 10 pages; 600 seconds; single recognition lock |
| User storage | 10 scores, 50 MB |
| Global storage | 50 scores, 250 MB |
| Artifact Registry | temporary digest; delete after verified release |
| Billing | $1 monthly gross budget; alerts at 1¢, 50¢, and $1 |
| Automatic stop | private min-0 Cloud Run guard; verified Pub/Sub event unlinks project billing |

The budget excludes credits when measuring thresholds. It is not a cap: usage
estimates and notifications can be delayed. Firebase Blaze, Cloud Run,
Firestore, GCS, networking, logs, Secret Manager, and Artifact Registry can
charge beyond allowances. Public availability cannot guarantee $0 under quota
changes or abuse.

The cost guard accepts authenticated same-project Pub/Sub push only. It checks
the exact billing account, budget ID/display name, schema version, USD currency,
fixed amount, and 100% threshold. Its dedicated identity has project Browser
and Project Billing Manager only; no billing-account role is granted. Delivery
is at least once, so the handler is idempotent and asks Pub/Sub to retry API
failures. The guard runs at min 0, max 1, concurrency 1, 512 MiB (the minimum
supported by Cloud Run's Gen2 execution environment).

This reaction is not a hard cap. Google budget estimates and notifications can
be delayed, and pre-shutdown usage can be reported afterward. Disconnection
stops all billable project services and can make resources unavailable or
non-recoverable. Activating it and the public deployment remains an
explicit-approval item.

## CI/CD trust model

GitLab CI performs Django checks/tests, frontend lint/tests/build, dependency
audits, a Firestore emulator lifecycle, digest-pinned Kaniko builds, protected
`main` deployment, and separate public verification.

GitLab OIDC exchanges through Workload Identity Federation; no JSON key exists.
CI copies the exact app and cost-guard images to temporary Artifact Registry,
deploys both by digest, configures authenticated Pub/Sub delivery, discovers/
publishes the app URL, creates and waits for the versioned Datastore indexes,
deploys Firebase, verifies health/session/frontend HTTPS, and removes both
temporary images. GitHub mirrors reviewed GitLab `main`.

The deploy container installs checksum-pinned Node.js 22 and builds
`frontend/dist` from the lock file. Its temporary external-account credential
uses this project for quota. Only the GitLab project principal set can consume
that quota and impersonate the deploy identity, and the WIF provider further
requires this repository's protected `main` branch.

## Deployment evidence

- Firebase Hosting serves the public HTTPS URL and rewrites `/api/**` to the
  deployed Cloud Run service.
- Firestore Datastore mode, the private GCS bucket, Secret Manager secret,
  runtime/deploy identities, and protected-main WIF provider are active.
- The application service is min 0/max 1/concurrency 4; the billing guard is
  private, min 0/max 1/concurrency 1, and invoked only by authenticated Pub/Sub.
- GitLab pipeline `3038775009` passed deployment and separate public
  verification; its temporary Artifact Registry images were removed.
- Automated backend and Firestore-emulator tests cover Google-token rejection,
  two-account isolation, PDF/OMR state, measure navigation APIs, practice
  create/remove, and complete score deletion.
