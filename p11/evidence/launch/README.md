# Public launch evidence

**Observed November 15, 2026.**

- Public URL: <https://music-companion-513717.web.app>
- Deployment commit: `dd3f56980fa14553a9f4238438102583dcd66254`
- Hosted frontend: Firebase Hosting
- API and recognition service: Cloud Run in `us-central1`
- Sign-in: verified Google ID token with a signed, secure session cookie

`public-google-sign-in-2026-11-15.png` is a browser capture of the public Google sign-in page. The public `/api/session/` endpoint reported `auth_mode: google` and `authenticated: false` before sign-in, confirming that the app did not expose a default mock identity.

The protected-main pipeline for this commit deployed the application and ran the public verification step successfully: [pipeline 3071046544](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3071046544).

The outside-user walkthrough remains an honest pending record in `p11/outside-user-test.md`.
