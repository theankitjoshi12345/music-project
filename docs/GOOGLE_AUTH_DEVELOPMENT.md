# Google authentication development setup

Project: `music-companion-513717` (Music Companion), project number
`620433654777`. This project is for development; no deployment or billing is
needed to configure the Google sign-in integration.

## Inspected configuration — November 4, 2026

- Project lifecycle state: ACTIVE; no parent organization was returned.
- The signed-in developer has the existing Owner role. The inspected project
  IAM policy has one user binding and no public principal binding.
- Billing is disabled (`billingEnabled: false`).
- Existing enabled APIs include BigQuery, Cloud Storage, Logging, Monitoring,
  Service Usage and related APIs. An enabled API is not proof of a deployed
  resource. None were enabled, disabled or deployed as part of this setup.
- Google Auth Platform initially reported that it was not configured.

## Development OAuth configuration

Use the app name **Score Companion (Development)** and the project owner's
Google account for the consent-screen support and developer contacts. Use
**External** audience with **Testing** publishing status. Add only intended
test accounts; adding a test user does not grant that person project IAM access.

The proposed OAuth client is a **Web application** named
**Score Companion Local Development**. Use these exact browser origins:

```text
http://localhost:5173
http://localhost:8080
```

Register these exact authorized redirect URIs:

```text
http://localhost:5173/accounts/google/login/callback/
http://localhost:8080/accounts/google/login/callback/
```

These paths are the intended django-allauth callback routes. The current app
does not implement them yet; registration alone does not make sign-in work.
Vite and Nginx must proxy the authentication routes to Django during integration.
The protocol, host, port and trailing slash must match Google's registration.

Request only basic identity scopes: `openid`, `email` and `profile`. Google
sign-in does not require access to Drive, Gmail, BigQuery or Cloud Storage.
No service-account key is needed for this browser sign-in flow.

Google permits HTTP localhost callbacks for development. Raw private IP
addresses are not valid callback hosts. Testing from another device requires
an approved HTTPS development domain or tunnel and matching callback registration.
Creating a tunnel or deploying a host is a separate action.

## Credentials and local development

Keep the OAuth client secret in backend-only local configuration or an OS
credential store. Do not put it in React code, a `VITE_` variable, Git, an image
build argument, logs or screenshots. The client ID may be used by an app, but
the client secret must stay server-side.

Git ignores `.env`, `.env.*`, `.secrets/` and downloaded `client_secret_*.json`
files while allowing environment examples. Docker's build context excludes
those secrets too. These ignore rules are safeguards, not a replacement for
reviewing staged files.

Cloud Shell already provides gcloud; installing a second CLI on the Mac is
unnecessary for this project audit. Use an explicit `--project=music-companion-513717`
for cloud commands or a named development configuration. Do not create a
service-account key or run an application-default login merely for Google sign-in.

## App integration still required

The running app currently uses mock profiles and a shared score library. Before
calling authentication complete:

1. Integrate Django/allauth and Google sign-in, session cookies, CSRF protection,
   logout and authenticated-user state in React.
2. Assign real user ownership to scores and practice marks, scope every API and
   image lookup, and protect original PDF downloads.
3. Make upload deduplication account-aware and migrate existing data explicitly.
4. Test two separate accounts, canceled sign-in, session expiry, logout, direct
   file URLs and cross-account access in native and Docker modes.
5. Configure HTTPS and deployment-specific allowed hosts, trusted origins and
   callback URLs before any public deployment.

The existing one-command Docker startup remains available. The containers were
left stopped at the user's request. OAuth configuration does not require them
to run.

## References

- [Google OAuth consent configuration](https://developers.google.com/workspace/guides/configure-oauth-consent)
- [Google web-server OAuth and redirect rules](https://developers.google.com/identity/protocols/oauth2/web-server)
- [django-allauth Google provider](https://docs.allauth.org/en/latest/socialaccount/providers/google.html)
