# Deployment scripts

The canonical deployment, security, cost, and verification documentation is in
the root [README](../README.md) and [architecture](../architecture.md).

- `provision-gcp.sh` performs one-time, owner-approved Google resource and IAM
  setup. It refuses to run unless billing, resource, and IAM approval guards are
  all explicit.
- `ci-deploy.sh` is called only by protected GitLab `main`. It uses GitLab OIDC,
  deploys the backend and private cost guard, configures authenticated budget
  notifications, deploys Firebase Hosting, verifies HTTPS, and removes both
  temporary Artifact Registry images.

Neither script links a billing account, upgrades a billing plan, deletes user
data, or creates a service-account key. The approved cost guard can unlink the
project after the verified $1 budget notification; doing so stops cloud
services and can make resources unavailable or non-recoverable. Do not run
provisioning until Firebase Terms, residual delayed-billing risk, public access,
automatic shutdown, and the listed least-privilege IAM bindings are approved.
