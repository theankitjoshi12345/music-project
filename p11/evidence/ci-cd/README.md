# CI and deployment evidence

The root [.gitlab-ci.yml](../../.gitlab-ci.yml) is the launch pipeline. Merge requests and `main` run backend tests, Firestore integration, frontend lint/tests/build, dependency and frontend-security scans, and container-image packaging. Protected `main` also deploys Cloud Run and Firebase Hosting, then verifies the public HTTPS frontend and session endpoint.

Current successful protected-main evidence:

- Commit: `dd3f56980fa14553a9f4238438102583dcd66254`
- Pipeline: [3071046544](https://gitlab.com/ull-gitlab/453/fa26/fa26-team-08/music-project/-/pipelines/3071046544)
- Successful jobs: backend tests, Firestore integration, frontend tests, dependency scan, frontend-security scan, four image builds, `deploy-production`, and `verify-production`.

GitLab authenticates deployment through OpenID Connect and Google Workload Identity Federation. No service-account JSON key is stored in the repository.
