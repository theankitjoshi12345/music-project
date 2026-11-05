# Public launch evidence

**Status: temporary free demo verified (November 5, 2026).**

URL: https://locate-valuation-using-donald.trycloudflare.com

The URL is a Cloudflare Quick Tunnel from the Docker Compose `tunnel` service.
It does not require an account, domain, billing, or a cloud VM. It is temporary
and remains available only while the local Docker tunnel container runs.

Verified over HTTPS:

- `/` returned HTTP 200 and the Score Companion application title.
- `/api/health/` returned HTTP 200 with `status: ok`.
- `/api/session/` created an isolated private browser session.
- A real uploaded PDF completed Audiveris recognition with 56 passages and
  layout version 1.
- A measure preview fetched through the public URL returned `image/png`,
  608 x 607 pixels, HTTP 200.
- Recreating the backend and frontend containers preserved two completed scores,
  112 passages, the latest source PDF, and its 191,436-byte metadata in the named
  Docker volume; the public health endpoint returned HTTP 200 after the correct
  free-demo overlay was restored.
- Two fresh HTTPS browser sessions were tested with a disposable upload. The
  owner received 200 for its score; the other session received an empty library
  and 404 for both read and delete; the owner deleted the record with 204 and a
  follow-up read returned 404.

The verification used Docker on November 5, 2026. Temporary test scores were
deleted through their authorized sessions; existing library entries were kept.
This is demo evidence, not a claim of permanent uptime, host-machine failure
recovery, or outside-user testing.

No screenshots are claimed here. Do not substitute localhost or P10 captures.
