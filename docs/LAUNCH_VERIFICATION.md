# Launch verification

Verified November 5, 2026 against merge commit
`8ec3e3b42e4f151afd1b14d3c13e64ab55f336c1`.

## Free public demo

- Temporary HTTPS URL: `https://locate-valuation-using-donald.trycloudflare.com`
- `/` and `/api/health/` returned HTTP 200 through Cloudflare Quick Tunnel.
- A real PDF completed Audiveris recognition with layout version 1 and 56
  passages; a public measure preview returned a 608 x 607 PNG.
- The URL exists only while the local Docker tunnel runs and may change after a
  tunnel restart. This is not permanent hosting or an uptime commitment.

## Persistence

Before and after recreating the backend and frontend containers, the named
Docker volume contained the same two completed scores, 112 passages, source PDF,
and 191,436-byte source metadata for the latest recognized score. The tunnel was
kept running and returned HTTP 200 after the documented free-demo overlay was
restored. This proves container-restart persistence, not recovery from loss of
the developer computer or Docker volume.

## Isolation and cleanup

Two fresh public HTTPS sessions exercised a disposable upload. The owner could
read it; the second session saw an empty library and received 404 for read and
delete. The owner deleted the score with HTTP 204, and a subsequent owner read
returned 404. Backend tests cover score, PDF, page, passage, practice, extraction,
CSRF, cookie, impersonation, quota, and deletion boundaries.

## Automated checks

- Backend: 54 tests passed; migrations check reported no changes.
- Frontend: 24 tests passed; lint completed with three non-blocking Fast Refresh
  warnings; the production build succeeded.
- Docker: backend and frontend health checks passed with the free-demo overlay.
- Repositories: local, GitLab `main`, and GitHub `main` resolve to the same merge
  commit above.

## GitLab CI status

`.gitlab-ci.yml` passes GitLab's static lint. Merge request !30 created pipeline
3032702793, but GitLab failed it before creating jobs. Merge request !31 switched
every active job from hosted runners to eight online ULL group runners; pipeline
3032789671 was still rejected before job creation. GitLab's simulation reports
that the account must complete identity verification to run CI. No successful
pipeline is claimed; after free account verification, rerun the pipeline.

No billing account, paid runner, cloud VM, or billable deployment was enabled.
