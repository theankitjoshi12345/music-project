# Score Companion

Score Companion turns uploaded sheet-music PDFs into navigable measures. A
musician can view the original notation, move by measure or page, save practice
items, and return to a private library. MusicXML, XML, and MXL imports are also
supported.

## Launch status

The application is live at
[https://music-companion-513717.web.app](https://music-companion-513717.web.app).
The public frontend, health endpoint, Google-auth session configuration, cloud
database migrations, and keyless deployment were verified on November 7, 2026.
Google Cloud project `music-companion-513717` has active Free Trial billing,
required service APIs enabled, and a project-scoped $1 budget that warns from
1 cent of **gross** usage (credits excluded).

The owner authorized up to $1/month. The budget is not a hard spending cap: a
billing-linked Firebase project uses Blaze even while no-cost quotas and trial
credits apply, and Google can report usage hours late. The deployment includes
a private automatic shutdown service that unlinks this project from billing on
the first verified notification at or above $1. Delayed usage can still make
the final amount exceed $1, so public deployment and its least-privilege IAM
changes were activated only after explicit owner approval.

## User flow

1. Sign in with Google in production; local demo mode has mock profiles.
2. Upload a PDF or MusicXML-family score up to 10 MB.
3. Poppler validates/renders PDFs and Audiveris identifies measures. The UI
   displays estimated and elapsed processing time.
4. View the original PDF with clickable measures; navigate by measure, page,
   section, jump form, or Left/Right arrow keys.
5. Save/remove a practice item, add a note, and mark it practiced.
6. Delete a score to remove metadata, practice records, original upload, and
   derived images.

OMR is an estimate and must be checked against the source. Score Companion
displays the original PDF rather than re-engraving recognized notes.

## One-command local start

Docker is the recommended team workflow. It includes React/Nginx, Django,
SQLite, Poppler, Java, and Audiveris; teammates install no OMR tools on the host.

```bash
docker compose up --build -d --wait
```

Open <http://localhost:8080/>.

```bash
docker compose ps
docker compose logs -f
docker compose down                 # preserves the app-data volume
```

Do not add `--volumes` unless you intend to erase the Docker library. Audiveris
is amd64, so Docker Desktop emulates the backend on Apple Silicon.

Trusted private-network access:

```bash
BIND_ADDRESS=0.0.0.0 \
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.203 \
docker compose up --build -d --wait
```

Replace the example IP and open `http://<private-ip>:8080/`. This is not the
public HTTPS deployment.

## Native local development

Native work requires Python 3.12+, Node.js, Poppler, and Audiveris. SQLite and
filesystem media are the defaults.

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py runserver
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open <http://localhost:5173/>. Vite proxies `/api/` to port 8000. Set
`AUDIVERIS_COMMAND` if it is not on `PATH`; macOS discovery also checks
`/Applications/Audiveris.app` and `.local-tools/Audiveris.app`.

## Production architecture

| Concern | Service/control |
| --- | --- |
| React/Vite | Firebase Hosting with SPA fallback |
| Django + OMR | Cloud Run, min 0, max 1, concurrency 1 |
| Metadata | Firestore in Datastore mode |
| PDFs/images | Private GCS bucket with public-access prevention |
| Identity | Verified Google ID token + signed secure cookie |
| Secret | Secret Manager; never committed or stored in GitLab |
| Build handoff | Temporary Artifact Registry image, deleted after verification |
| Deployment | Protected GitLab `main`, OIDC/WIF, no JSON key |
| Cost stop | Private Cloud Run guard + authenticated budget Pub/Sub push |

Firebase rewrites ordinary `/api/**` calls to Cloud Run so cookies stay
same-origin. Hosting limits rewritten requests to 60 seconds, while Audiveris
may need several minutes. The browser therefore requests a signed 15-minute,
owner-and-score-bound ticket and sends only the long OMR call directly to Cloud
Run. CORS accepts only the two Firebase origins, and the ticket cannot access a
different score or general endpoint.

Firebase Hosting forwards only its specially named `__session` cookie to a
rewritten Cloud Run request. Production therefore uses that name for Django's
signed, secure, HTTP-only Google session; local development keeps Django's
normal `sessionid` cookie.

See [architecture.md](architecture.md) for the detailed data and trust model.

## Authentication and isolation

`DJANGO_AUTH_MODE` supports `demo` locally, compatibility `session`, and
production `google`. Google mode verifies the ID-token audience and
`email_verified`, then hashes the stable `sub` as the owner key. Email/name are
display-only.

Production cookies are HTTP-only, Secure, SameSite=Lax, signed, and protected
by CSRF checks. Files are never public URLs; Django streams them after the owner
check. Tests cover signed-out and tampered-token rejection, two-account
isolation, logout/re-login, and owner-bound OMR tickets.

## Production environment and limits

Deployment supplies:

- `DJANGO_ENV=production`, `DJANGO_DEBUG=false`, `DJANGO_AUTH_MODE=google`,
  `DJANGO_ADMIN_ENABLED=false`.
- Explicit allowed hosts, Firebase-only CORS/CSRF origins, and the discovered
  `CLOUD_RUN_PUBLIC_URL`.
- Firestore Datastore mode, GCS storage, project/bucket names, OAuth client ID,
  and a Secret Manager reference for `DJANGO_SECRET_KEY`.
- 10 PDF pages, 600-second OMR timeout, 120 API requests/hour, 4 uploads/day,
  and 2 OMR jobs/day per account/IP guard.

Storage ceilings are 10 scores/50 MB per account and 50 scores/250 MB globally.
Each file is limited to 10 MB.

## Verification

```bash
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
backend/.venv/bin/python backend/manage.py test scoreapi
cd frontend && npm ci && npm run lint && npm test && npm run build
```

The Firestore emulator smoke test exercises migrations, account isolation,
uploads, passages, practice create/delete, and complete score deletion. It
refuses to run without `DATASTORE_EMULATOR_HOST`.

Firebase Hosting can be checked without cloud deployment after building Vite:

```bash
npx --yes firebase-tools@15.35.0 emulators:exec \
  --only hosting --project demo-music-companion \
  "curl --fail --silent http://127.0.0.1:5005/ | grep -q 'Score Companion'"
```

## CI/CD and repositories

GitLab is authoritative; GitHub mirrors reviewed `main`. CI runs backend,
frontend, security, and Firestore-emulator checks; builds pinned amd64 images
with daemonless Kaniko; and deploys only from protected `main` when
`DEPLOY_ENABLED=true`.

Deployment exchanges a GitLab OIDC token through Workload Identity Federation,
copies the exact application and cost-guard images to Artifact Registry,
deploys both Cloud Run services by digest, deploys `frontend/dist` to Firebase,
verifies frontend/API HTTPS, and deletes both temporary images.
`CLEAN_ARTIFACT_IMAGE=true` is mandatory.

The deploy job downloads checksum-pinned Node.js 22, builds Vite from the lock
file, and gives its short-lived external-account credential an explicit quota
project. The GitLab-project principal set has only Workload Identity User on
the deploy identity and Service Usage Consumer on this project; the provider
also requires this repository's protected `main` branch. No service-account
key or Firebase refresh token is stored in GitLab.

```text
frontend/          React UI and tests
backend/           Django API, OMR, persistence, storage, tests
firebase.json      Hosting, Cloud Run rewrite, caching
Dockerfile         local images and backend-only Cloud Run target
compose.yaml       one-command local stack
deploy/            guarded provisioning and CI deployment
.gitlab-ci.yml     tests, builds, deployment, verification
architecture.md    runtime/data/security design
```

## Cost boundary

No public Blaze design can guarantee a mathematical $0: pricing can change,
abuse can consume quotas, and billing data is delayed. Protections are
scale-to-zero, one maximum instance, one concurrent request, bounded storage
and PDFs, strict action rates, temporary images, and gross-usage alerts.

The automatic guard validates the billing account, budget ID and name, schema,
USD currency, fixed $1 amount, and 100% threshold. Only an authenticated
same-project Pub/Sub identity can invoke its private Cloud Run endpoint. Its
runtime identity receives project Browser plus Project Billing Manager; it has
no billing-account role and can unlink only this project. Duplicate delivery is
idempotent and failures are retried.

This is the strictest practical stop, not a guarantee: Google says budget data
and Pub/Sub delivery can be delayed, and charges incurred before unlinking can
arrive later. Unlinking stops the app and may make cloud resources unavailable
or non-recoverable. It is therefore activated only with explicit approval.
