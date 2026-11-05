# Score Companion

Score Companion is a CMPS 453 team project for uploading sheet music, viewing
individual measures, and saving passages and notes for practice.

## USER GUIDE

**Public launch status:** temporary free demo verified at
<https://locate-valuation-using-donald.trycloudflare.com> while the Docker tunnel
is running. The address is temporary and changes after restart. Instructions are
in [Free demo sharing](docs/FREE_DEMO.md).
The Google Cloud VM proposal is paid and out of scope for the free-only launch;
see [Cloud deployment](#cloud-deployment) for the record. Assignment evidence is indexed in
[p11/README.md](p11/README.md); completed P#10 files remain unchanged.

The app includes Logan's Offline Score Library, Ankit's Score Viewer & Navigation,
Matthew's Measure Marker, and Jonathan's Practice Review. The current flow is:
upload a score, select a measure, save it for practice, then review it or return
to its original score context. Despite the original screen name, browser offline
caching is not implemented.

Local development uses mock profiles: choose **Alex Rivera** or **Sam Lee** in
**Practice profile**. They share a local library and have separate practice lists.
Never publish this demo mode. Production mode instead creates a private,
server-issued browser session. Scores, originals, images, and practice records
are isolated to that session; a forged profile header grants no access.
Keep this browser's cookies to return to your library. Access expires after
30 days of inactivity, with no account recovery or cross-device synchronization.
This is anonymous course-demo access, not a verified Google account.

The Google sign-in development project and intended local callback configuration
are documented in [Google authentication development setup](docs/GOOGLE_AUTH_DEVELOPMENT.md).
Google sign-in is not implemented in the app yet.

Use **Add to library** to upload a PDF, MusicXML, XML, or MXL file (up to 10 MB).
PDF uploads open the reader and start local Audiveris recognition automatically.
Detected measures appear next to the PDF, grouped by page. Use **Save for practice**
beside the selected measure, then **Practice review** in the header to revisit it. Selecting a measure opens
its actual music cropped from the uploaded PDF, including all instrument staves
in that measure. **Full page** displays the original page with clickable measure
regions. Check recognition boundaries and numbering against the original score.
MusicXML/XML/MXL uploads import structured metadata directly.

While finding measures, the reader shows an **estimated countdown** and elapsed
time. It checks the PDF's real page count early and uses the server's conversion
start time, so refreshing or returning to the score keeps the clock. Estimates
account for the slower Docker runtime. If the estimate runs out, the reader says
**Taking longer than estimated** and keeps showing elapsed time until the server
finishes or reports an error. You can read the full page while this runs.
Conversion actions from the library open this reader immediately; on phones the
progress card appears before the score image.

The reader provides a retry action on failure. **Remove from practice** in the
reader, marker, or review screen deletes that user's saved practice row and note
from the backend. The score and its measures remain available in Library.
Under **Library → Score options → Delete score**, deleting a score removes the
uploaded file, score record, measures, and every attached practice mark.

All screens share Library and Practice review navigation. The reader groups
previous/next measure controls and the practice action beside the selected
notation. **← / →** move between measures across page boundaries; they do not
intercept typing in fields. **Go to measure** jumps directly to a number.
Full-page view has its own page controls. The separate Practice marker is
available under a score's options.

The interface uses a colorful practice-studio style with an original music-note
and sparkle logo. **Theme** in the header offers **Violet Jam**, **Peach Pop**,
and **Mint Groove**. The choice stays in this browser across navigation and
reloads; it does not change your scores or practice profile. All palettes keep
the original sheet music on white paper. Fonts are bundled with the app, so
teammates need no font installation or external font service.

The library introduces the three steps: add sheet music, choose a measure, save
it for practice. After saving, **Open practice list** beside the selected measure
takes you directly to review. **Mark practiced** records completion;
**Practice again** puts it back on your to-practice list. Removal still deletes
the saved row and note from the backend.

Data and image loads show skeleton placeholders. Save, mark practiced and remove
actions show a pending state and wait for backend confirmation before changing
the displayed saved state. Failed requests keep the existing item and offer a
retry. See the [navigation and usability check](docs/UI_REVIEW.md).

Uploading an identical file reopens its existing library entry and keeps its
measures and practice notes. Different files with the same original filename
are stored separately. Database failures clean up the newly written file.

Uploaded PDFs display directly in the Score Viewer. Use the viewer page controls
to move through the document or open the original PDF in a new tab.
Existing PDFs imported without page coordinates automatically prepare previews
when opened. Existing practice marks retain their passage IDs during this upgrade.

### PDF recognition and rendering

Native PDF measure recognition requires local Poppler (`pdftoppm` and `pdfinfo`)
and Audiveris. Docker installs both in its backend image automatically. Page and
measure images also require Poppler. For native setup, set `AUDIVERIS_COMMAND`
to the executable, or install it on PATH. On macOS the app also checks
`/Applications/Audiveris.app` and `.local-tools/Audiveris.app` in this checkout.
The mounted installer is not used as the runtime. The binary is local-only and
excluded from Git; another native installation must install it separately.

The demo limits recognition to PDFs with at most 10 pages and bounds rendering
and recognition time. A second request for the same score shares the processing
state; completed imports are reused. Failed/repeated extraction preserves
existing measures and practice notes. Audiveris is an external AGPL-3.0 application;
see its [source and license](https://github.com/Audiveris/audiveris).

## Tech stack

| Area | Choice |
| --- | --- |
| Frontend | React + Vite (JavaScript) |
| Backend | Django + Django REST Framework |
| Database | SQLite |
| Runtime | Python 3.12+ and Node.js LTS |
| PDF pipeline | Poppler + local Audiveris; original PDF crops rendered as PNG |
| Version control | GitLab merge requests + GitHub mirror |
| UI reference | [Score Companion Figma design](https://www.figma.com/design/NSZliKsVC3CiwrjqQfrOHS) and export: `p9/Score_Companion_P8_Revised_Screens.pdf` |

See [architecture.md](architecture.md) for the implemented data flow, persistence,
runtime limits, and remaining boundaries.

## Screen ownership

| Owner | Assigned screen | Complexity | Route |
| --- | --- | --- | --- |
| Ankit Joshi | Score Viewer & Navigation | Hardest | [`#/score-viewer`](http://localhost:5173/#/score-viewer) |
| Matthew Pisani | Measure Marker | Hard | [`#/measure-marker`](http://localhost:5173/#/measure-marker) |
| Jonathan Dempsey | Practice Review | Medium | [`#/practice-review`](http://localhost:5173/#/practice-review) |
| Logan Broussard | Offline Score Library | Easiest | [`#/score-library`](http://localhost:5173/#/score-library) |

All four screen routes are implemented. The Score Viewer displays uploaded PDFs
and their detected measures with practice actions. Measure Marker and Practice
Review use the shared backend for the selected demo user's practice marks.

## Project structure

```text
frontend/                       React + Vite application
  src/App.jsx                   Hash routes and demo-user isolation
  src/OfflineScoreLibrary.jsx    Upload, reopen, and delete scores
  src/pages/ScoreViewer.jsx      Score navigation and practice actions
  src/pages/PdfScoreReader.jsx   Measure crops and full-page overlays
  src/PracticeReview.jsx         Saved passages, notes, and resolution
  src/components/score-companion/  Shared UI components and usage guide
backend/                        Django project
  config/                       Settings and root routing
  scoreapi/                     REST API, models, migrations, and tests
    upload_service.py           Deduplication and upload cleanup
    extraction_service.py       Extraction state and passage persistence
    score_extract.py            MusicXML and Audiveris layout import
    pdf_render.py               Original PDF page and measure images
  media/                        Local uploaded files (ignored by Git)
  requirements.txt              Backend dependencies
  requirements-docker.txt       Additional Gunicorn dependency for Docker
.local-tools/                   Optional local Audiveris install (ignored)
Dockerfile                      Frontend and backend image stages
compose.yaml                    One-command startup and persistent volume
docker/                         Container entrypoint and Nginx configuration
p9/                             Revised Figma PDF and P#9 instructions
p10/                            P#10 instructions and report
architecture.md                 Implemented architecture and limits
API_CONTRACT.md                 REST endpoints and data contract
```

## LOCAL DEVELOPMENT

Choose either startup option below. Both run the complete library, PDF measure
reader, and practice flow. Local development uses two terminals; Docker Compose
starts both services with one command.

| Option | Install on the host | App URL |
| --- | --- | --- |
| Local development | Python, Node.js, Poppler, Audiveris and its Java runtime | http://localhost:5173/ |
| Docker Compose | Docker with Compose; no separate Python, Node.js, Java, Poppler or Audiveris install | http://localhost:8080/ |

### Option 1: local development

#### Prerequisites

- Python 3.12 or newer
- Node.js LTS
- Git
- Poppler and Audiveris for the PDF measure flow described above

Install Poppler through your system package manager (for example, `brew install
poppler` on macOS). Install Audiveris separately with a compatible Java runtime;
the local demo was verified with Audiveris 5.11 and its bundled Java runtime.
The application can discover its macOS installation automatically. For another
location, set the executable before starting Django:

```bash
export AUDIVERIS_COMMAND="/absolute/path/to/Audiveris"
```

#### Backend (terminal 1, repository root)

```bash
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python backend/manage.py migrate
backend/.venv/bin/python backend/manage.py runserver
```

Migrations include the stored measure-coordinate schema. Existing installations
can also run `backend/.venv/bin/python backend/manage.py index_score_files` once
to fingerprint legacy uploads for deduplication; this does not merge or delete
existing scores. No sample scores are inserted during startup.

The API runs at `http://127.0.0.1:8000/`. Confirm it with:

```bash
curl http://127.0.0.1:8000/api/health/
```

#### Frontend (terminal 2, repository root)

```bash
cd frontend
npm ci
npm run dev
```

Vite serves the app at `http://localhost:5173/` and proxies `/api/` and `/media/`
to Django at `127.0.0.1:8000`. Keep both servers running.

For access from another device on the same network, start Django with
`backend/.venv/bin/python backend/manage.py runserver 0.0.0.0:8000` and Vite
with `npm run dev -- --host 0.0.0.0`. Open `http://<your-private-ip>:5173/`
on that device. This is a local development server with demo authentication.

### Option 2: Docker Compose

Install and start [Docker Desktop](https://docs.docker.com/desktop/) on macOS or
Windows, or Docker Engine with the Compose plugin on Linux. From the repository
root, run this single command:

```bash
docker compose up --build -d --wait
```

Open **http://localhost:8080/**. No environment file or manual migration is
required. The first build needs internet access to download images, packages,
and the verified Audiveris installer and can take several minutes. Later starts
reuse cached images.
Docker Desktop must be running before this command.

Compose starts two services:

- `frontend`: builds React with Node, then serves the production files with
  Nginx and proxies API requests to Django.
- `backend`: Python 3.12, Django/Gunicorn, Poppler, Audiveris 5.11.0, and the
  installer's bundled Java runtime. Startup applies migrations, collects static
  files, and creates a secret key in persistent storage.

Health checks make `--wait` return after the API is ready through Nginx. The API
has no separate host port. The app binds to localhost by default. Port 8080 is
separate from the manual setup, so both options can run at the same time.

Audiveris's official Linux installer is x86_64, so the backend explicitly uses
`linux/amd64`. Docker Desktop runs it through emulation on Apple Silicon; OMR
can be slower than the native local setup. The frontend uses the host's native
container architecture. The Mac `.local-tools` application is never copied into
the Linux image. See [third-party notices](THIRD_PARTY_NOTICES.md).

Database, source PDFs, collected static files, and the generated Django secret
key live in the named `app-data` volume under `/data`. It starts as an empty
library and is separate from `backend/db.sqlite3` and `backend/media/` used by
the manual setup. Changing startup options does not transfer existing data.
Ordinary container replacement and `docker compose down` retain this volume.
Do not add `--volumes` to `down` unless you intend to erase the Docker library.

```bash
docker compose ps                  # Service health and published port
docker compose logs -f             # API, recognition and proxy logs
docker compose down                # Stop; keep database and uploads
docker compose up --build -d --wait # Start again or rebuild after code changes
```

To use another port:

```bash
PORT=8081 docker compose up --build -d --wait
```

For another device on your private network, replace the example address with
this computer's private IP, start with the following environment values, and
open `http://<your-private-ip>:8080/`:

```bash
BIND_ADDRESS=0.0.0.0 DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.203 docker compose up --build -d --wait
```

These environment prefixes use POSIX shell syntax (macOS/Linux/WSL). The default
one-command startup also works in PowerShell. This remains the local team demo
with mock users. A public deployment still needs HTTPS, real access control, and
a durable background queue for recognition. Recognition currently runs inside
the API request. Docker allows up to 600 seconds for Audiveris and uses
720-second Nginx/Gunicorn timeouts for the full bounded pipeline; native
development retains its 300-second Audiveris default.

#### Docker configuration

| Variable | Default / purpose |
| --- | --- |
| `PORT` | `8080`; published frontend port |
| `BIND_ADDRESS` | `127.0.0.1`; set to `0.0.0.0` for LAN access |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]`; include your LAN IP or deployment hostname |
| `DJANGO_DEBUG` | Set to `false` by Compose; manual startup defaults to `true` |
| `DJANGO_DATA_DIR` | `/data` in Docker; manual startup defaults to `backend/` |
| `DJANGO_SECRET_KEY_FILE` | `/data/django-secret-key`; created once and reused |
| `OMR_TIMEOUT_SECONDS` | `600` in Compose; `300` by default for native development |
| `OMR_ESTIMATED_SECONDS_PER_PAGE` | Countdown estimate: `150` in Compose, `15` natively; configurable for faster/slower servers |

The Docker build excludes local databases, uploaded music, `.local-tools`, Git
history, local environment files, and course-report folders. Migrations and
application source are included. Local environment overrides are optional;
the defaults preserve the existing manual setup.

### P#10 smoke test

With either setup running (port 5173 manually, or port 8080 with Docker):

1. Open `/#/score-library` at your chosen app URL, choose Alex Rivera, and upload
   a clear sheet-music PDF of at most 10 pages. Wait for recognition to finish.
2. Select different measure numbers. Confirm the music image changes and
   includes all staves, as well as showing the correct measure and page label.
3. Use **Next**, **Previous**, or the arrow keys to cross a page boundary.
   Switch to **Full page**, select a highlighted measure
   region, and confirm its selected-measure preview loads.
4. Use **Save for practice**, open **Practice review**, confirm the saved measure, and
   resolve the mark.
   Use **Open measure** to return to the exact saved measure and page.
5. Switch to Sam Lee and confirm Alex's marks do not appear. Reuploading the
   identical PDF should reopen its existing library entry with its data intact.
6. Remove a practice item, reload the reader and review, and confirm it is
   unsaved while the score is still available. Then, with a disposable upload,
   use **Score options → Delete score** and confirm the library entry,
   original file, passages, and attached practice marks are removed.

### Score Viewer navigation

Open `http://localhost:5173/#/score-viewer`. To open a particular API score,
use `#/score-viewer?score=1` (replace `1` with its database ID). Library
integration can link to this route without changing the viewer.
Practice Review includes `&passage=<id>` to reopen the saved passage's page
within its original score.

The viewer requests the selected score and its passages through `/api/`; Vite
proxies these requests to Django at `127.0.0.1:8000`. Start both servers for
live data. An empty library asks you to add a score; it does not insert demo
content. Failed requests show a retry action and a return link to the library.

The original PDF provides the music notation. Audiveris supplies the measure
metadata and coordinates; Django renders each selected region from the original
PDF as a PNG. Full-page overlays use those same coordinates. Non-PDF metadata
previews use illustrative notation. OMR boundaries and numbering need visual
review against the source score.

Page, section, and measure jumps smoothly scroll and highlight the destination
measure so it remains easy to keep visual context while navigating a score.

### Verification status

Both startup options were verified on November 3, 2026:

| Setup | Checks completed |
| --- | --- |
| Native | Fresh migrations and separate Django/Vite processes; real PDF upload and Audiveris recognition; all 56 measure buttons loaded distinct images; both page overlays; practice save, resolve, return, user isolation, duplicate upload and deletion |
| Docker | One-command build/start with both services healthy; the same PDF/browser flow through Nginx; all 56 measure images; original PDF and collected static files served with DEBUG disabled |
| Docker persistence | Compose down followed by the one-command build/start; exact PDF bytes, 56 passages, saved/resolved mark and generated secret key survived; saved passage reopened in the browser after recreation |

The native browser check used an isolated data directory. The Docker check used
its separate named volume. Disposable scores and practice marks were deleted
after testing. The native library was preserved. Selected notation crops and
browser screenshots were visually checked.

The navigation/removal walkthrough also passes in both runtimes. It verifies
arrow keys, form-field protection, visible skeletons, failed deletion recovery,
permanent mark/note removal, user isolation and responsive layouts at 390, 768
and 1440 pixels. The four-screen flow is documented in [UI review](docs/UI_REVIEW.md).

Those historical checks preceded the P#11 security changes. Current launch
verification is recorded in [docs/LAUNCH_VERIFICATION.md](docs/LAUNCH_VERIFICATION.md).
The frontend production build and automated tests remain required in GitLab CI. Lint
reports three existing Fast Refresh warnings in `mockSession.jsx`. Recognition
results still need review for each new score; the successful demo PDF does not
guarantee OMR accuracy on other files.

To repeat the automated checks:

```bash
backend/.venv/bin/python backend/manage.py test scoreapi
backend/.venv/bin/python backend/manage.py makemigrations --check --dry-run
npm test --prefix frontend
npm run lint --prefix frontend
npm run build --prefix frontend
```

With Docker running, backend checks can also run inside its installed runtime:

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test scoreapi
```

The optional browser workflow test uses a separate, empty library and a real
sheet-music PDF supplied by the tester. It covers navigation, conversion timing,
loading skeletons, keyboard/form behavior, removal failures, user isolation,
mobile/tablet layouts and backend/file cleanup. Use a separate Compose project:

```bash
PORT=8081 docker compose -p score-companion-e2e up --build -d --wait
cd frontend
npm ci
npx playwright install chromium
E2E_ORIGIN=http://localhost:8081 E2E_PDF=/absolute/path/to/score.pdf npm run test:e2e
```

The script refuses to run against a nonempty library, and deletes its own
uploaded score after the test. `E2E_EXPECTED_MEASURES=56` optionally checks the
benchmark's recognized count. To use installed Chrome, set
`E2E_BROWSER_CHANNEL=chrome`. Screenshots go to ignored `tmp/e2e/`; no video is
recorded. Normal Docker startup still requires only Docker.

### Reusing frontend components

The viewer is composed from shared layout, heading, feedback, score context,
navigation, score sheet, measure preview, and measure-jump components.
See the [component usage guide](frontend/src/components/score-companion/README.md)
for props and examples for the other screen owners. Components accept data and
callbacks; each owner keeps their own API integration and screen behavior.

## API

The Django REST API is documented in [API_CONTRACT.md](API_CONTRACT.md).
The library upload flow creates scores and imports passages. Endpoints under
`/api/` provide scores, passage metadata, extraction state, practice marks, full
PDF page images, and individual measure previews.

## CLOUD DEPLOYMENT

**Paid path, intentionally disabled:** `compose.production.yaml` and `deploy/` provide a
single-host deployment on an x86 Google Compute Engine VM. Provisioning has not
run: the project `music-companion-513717` has billing disabled. No deployment URL
should be treated as real until HTTPS and the full PDF workflow pass.

The proposed host is one **e2-medium (4 GiB RAM)** in `us-central1-a`, with a
20 GiB persistent disk and external IPv4. Caddy terminates HTTPS, Nginx serves
React, and Gunicorn runs Django with Poppler/Audiveris in Docker. SQLite, original
PDFs, sessions, and the Django key persist under `/srv/music-companion/data`.
Generated images are rendered on demand; recognition scratch files are removed
automatically. No developer computer is part of the proposed public runtime.

This preserves the existing relational model and filesystem-based OMR pipeline.
These resources are not free tier and are not part of the free-only launch.
Firestore is not a Django ORM replacement; Cloud Run's ephemeral filesystem cannot
hold this SQLite/media setup durably. A single persistent VM is appropriate for
this small course demo; horizontal scaling and high availability are not supported.

The proposed VM is **not free tier**. Current indicative cost is about **$29/month**
or **$4.75 for five continuous days**, before network egress and taxes; these are
estimates, not spending caps. Disk and reserved IP charges can continue while the
VM is stopped. No billable resources or billing account are created automatically
by ordinary CI. See [deployment operations and cost sources](deploy/README.md).

### Production prerequisites and procedure

1. Approve and link billing, the reviewed VM/network resources, and narrowly scoped
   GitLab deployment IAM. The provisioning script refuses to run without explicit
   `BILLING_APPROVED=true`; this flag alone is not user approval.
2. Follow [deploy/README.md](deploy/README.md) to provision, verify SSH host keys,
   and configure protected GitLab variables and workload identity federation.
3. Use the immutable images built by GitLab after backend/frontend tests and
   dependency audits. The protected main pipeline deploys only when the operator
   sets `DEPLOY_ENABLED=true` after approval.
4. Verify HTTPS, upload, actual recognition, measure PNGs, practice persistence,
   two-browser privacy, and container replacement before recording launch.

The proposed no-purchase hostname uses `sslip.io` with the reserved IP and a
publicly trusted certificate. Compute Engine does not supply a public HTTPS app
hostname; this is an explicit exception to the preferred platform domain, and
introduces a third-party DNS dependency. No hostname has been provisioned yet.

### Production configuration and security

| Setting | Production value or purpose |
| --- | --- |
| `DJANGO_ENV` / `DJANGO_DEBUG` | `production` / `false`; unsafe combinations fail startup |
| `DJANGO_AUTH_MODE` | `session`; local mock headers cannot select public users |
| `DJANGO_ALLOWED_HOSTS` | Exact public hostname plus internal health-check hosts |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Exact `https://` origin |
| `DJANGO_TRUST_PROXY` | `true` only behind the private trusted gateway |
| `DJANGO_SECRET_KEY_FILE` | `/data/django-secret-key`, private persistent generated key |
| `DJANGO_DATA_DIR` | `/data`, backed by the persistent VM disk |
| `PUBLIC_HOST` / `ACME_EMAIL` | Public DNS name and certificate renewal contact |
| `OMR_TIMEOUT_SECONDS` | 600 seconds, one recognition process at a time |

The gateway publishes only 80/443; API and database ports remain private. Admin
and direct `/media/` URLs are blocked. Original files use authorized API downloads.
Secure HttpOnly session cookies, CSRF enforcement, HTTPS redirects, HSTS, upload
size/type parsing bounds, and per-browser/global storage quotas protect the demo.
The backend container runs as an unprivileged user. Service-account JSON keys and
OAuth secrets never enter images or frontend bundles.

Anonymous session access is deliberately limited: lost/expired cookies cannot
recover a library, and automated abuse can exhaust the bounded demo capacity.
There is no billing hard cap, user account recovery, or independent backup service.
Deployments take a consistent backup before migrations; the backup is on the same
disk and does not protect against disk loss. Do not delete user data to clear
capacity without explicit authorization. Google sign-in remains separate, unfinished
integration work. See [architecture.md](architecture.md) for the trust boundaries.

### CI/CD and troubleshooting

`.gitlab-ci.yml` is the only deployment pipeline. It runs Django checks/tests,
React lint/tests/build, dependency audits, and immutable amd64 image builds.
Approved production deployment uses short-lived GitLab OIDC/WIF credentials and
IAP SSH with pinned host keys; post-deploy jobs check HTTPS frontend and API.
GitHub is a source mirror and has no competing deploy workflow.

If public deployment is skipped, check `DEPLOY_ENABLED`, protected-main status,
and the variables in the deployment guide. A green test pipeline with deployment
skipped does not mean the app is live. A 403 in a private library usually means
missing session/CSRF state; reload the app without clearing its cookies. A busy
conversion means another score holds the single OMR slot; retry after it finishes.
Check `docker compose ... logs backend` for bounded recognition errors. Never use
`down --volumes`, delete the persistent directory, or restore a database over
newer user data as an ordinary troubleshooting step.

## Development workflow

1. Work on a focused branch and use the assigned issue for context when available.
2. Use the revised Figma PDF as a reference alongside the implemented user flow.
3. Update affected API, README, and architecture documentation with the change.
4. Run relevant tests and verify the affected browser flow.
5. Open a GitLab merge request with validation results and issue links.
6. Merge verified work according to the agreed review process, then synchronize
   local `main` and the GitHub mirror with GitLab `main`.

## Prior project work

- [P#7 product overview and contributions](p7/P7-Team08/README.md)
- [P#7 report](p7/P7-Team08/P7-Team08-Report.pdf)
- [P#8 synthesis and implementation decisions](p8/P8_SYNTHESIS_AND_IMPLEMENTATION.md)
- [P#8 user-testing report](p8/P8_User_Testing_Report.pdf)
- [P#9 instructions](p9/instruction.md)
- [P#10 instructions](p10/instruction.md)

## License

See [LICENSE](LICENSE). The license covers only Ankit Joshi's original contributions. Team work, research records, participant material, and course-provided documents are excluded unless separately licensed.
