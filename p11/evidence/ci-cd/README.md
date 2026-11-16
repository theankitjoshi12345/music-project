# CI and deployment evidence

The root [.gitlab-ci.yml](../../.gitlab-ci.yml) is the launch pipeline. Merge requests and `main` run backend tests, Firestore integration, frontend lint/tests/build, dependency and frontend-security scans, and container-image packaging. Protected `main` also deploys Cloud Run and Firebase Hosting, then verifies the public HTTPS frontend and session endpoint.

Current successful protected-main evidence:

- Commit: `93e9de01675c007b29d0ed76609bb9463bb6098c`
- Pipeline: [3072113477](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3072113477)
- Successful jobs: backend tests, Firestore integration, frontend tests, dependency scan, frontend-security scan, four image builds, `deploy-production`, and `verify-production`.

GitLab authenticates deployment through OpenID Connect and Google Workload Identity Federation. No service-account JSON key is stored in the repository.
