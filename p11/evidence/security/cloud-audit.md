# Production security summary

**Observed from the deployed configuration on November 15, 2026.**

- Firebase Hosting serves the public HTTPS frontend; HTTP Strict Transport Security is present on the public response.
- Cloud Run runs with `DJANGO_AUTH_MODE=google` and `DJANGO_DEBUG=false`.
- Google identity tokens are verified on the server. A signed, HTTP-only, Secure, SameSite=Lax `__session` cookie carries the production session.
- Each score, passage, practice mark, file, page image, and measure preview is owner-scoped. The client never receives a storage or deploy credential.
- Firestore Datastore stores metadata and the GCS bucket stores files privately; Django authorizes file and preview responses.
- `DJANGO_SECRET_KEY` is a Secret Manager reference. GitLab deployment uses Workload Identity Federation instead of a committed service-account key.
- PDF/XML inputs, uploads, rendering, and recognition are bounded; one recognition lock protects the Audiveris process.

Residual limitations: this project is a class launch, not a penetration test or compliance certification. Optical music recognition can need human correction.
