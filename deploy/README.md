# Deployment scripts

The canonical deployment, security, cost, and verification documentation is in
the root [README](../README.md) and [architecture](../architecture.md).

- `provision-gcp.sh` performs one-time, owner-approved Google resource and IAM
  setup. It refuses to run unless billing, resource, and IAM approval guards are
  all explicit.
- `ci-deploy.sh` is called only by protected GitLab `main`. It uses GitLab OIDC,
  deploys the backend-only Cloud Run image and Firebase Hosting build, verifies
  HTTPS, and removes the temporary Artifact Registry image.

Neither script links a billing account, upgrades a billing plan, deletes user
data, or creates a service-account key. Do not run provisioning until Firebase
Terms, residual Blaze cost risk, and the listed least-privilege IAM bindings
have been reviewed and approved.
