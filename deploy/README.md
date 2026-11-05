# Deployment operations

Status: these assets prepare a deployment; they do not establish that a public application is live. Billing, provisioning, IAM, live HTTPS, and the cloud golden path must be verified before recording a launch URL.

## Proposed course-demo host and approval boundary

Use one Ubuntu 24.04 amd64 Compute Engine VM named `music-companion-demo` in `music-companion-513717`, zone `us-central1-a`: `e2-medium`, 4 GiB RAM, a 20 GiB `pd-standard` boot disk, and a reserved regional external IPv4 address. The VM has deletion protection, a retained boot disk, Shielded VM controls, OS Login, and no attached service account. A dedicated VPC permits public TCP 80/443 and SSH only through IAP's `35.235.240.0/20` range. No load balancer, Cloud SQL, Cloud NAT, paid vulnerability scanner, or purchased domain is required.

This is a **paid deployment proposal**, not an Always Free VM. As checked November 4, 2026, Iowa on-demand `e2-medium` costs $0.03350571/hour, in-use external IPv4 $0.005/hour, and standard disk $0.04/GiB-month beyond eligible free allowance. At 730 hours/month, 20 GiB at full disk price gives approximately **$28.91/month**, or **$4.75 for five continuous days**, before network egress, taxes, backups outside the VM, or other project usage. Eligible unused 30 GiB-month standard-disk allowance can reduce this estimate by $0.80/month. Compute and IPv4 remain chargeable. Stopping the VM stops compute charges; its retained disk and attached reserved IP remain allocated and may still cost money. An unassigned reserved IP has a higher price. A budget alert does not stop this VM.

Official pricing: [VM pricing](https://cloud.google.com/products/compute/pricing/general-purpose?hl=en), [disk pricing](https://cloud.google.com/compute/disks-image-pricing), [IPv4 pricing](https://cloud.google.com/vpc/network-pricing), [free-tier conditions](https://docs.cloud.google.com/free/docs/free-cloud-features). Recheck the Console estimate before provisioning.

This preserves the working SQLite ORM, local file paths, and x86 Audiveris runtime. Cloud Run would require external PostgreSQL and object-storage integration because its filesystem is ephemeral. For this small demo, a single persistent host avoids that migration and another vendor account. It is not a highly available or horizontally scalable deployment. The machine exposes two shared vCPUs with approximately one sustained core; recognition can take longer than a developer's machine.

The proposed hostname is `music-companion.<reserved-IP>.sslip.io`. Compute Engine supplies internal DNS, not a managed public HTTPS application hostname. This is an explicit exception to the assignment mission's preference for platform-provided domains: the independent free DNS service maps an embedded IP to that IP, and Caddy obtains/renews a public certificate. There is no domain purchase or DNS account. DNS availability and certificate-authority rate limits remain external dependencies. See [sslip.io/nip.io](https://nip.io/) and [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https). Never present the hostname template as a verified application link.

## One-time infrastructure setup

The project owner must approve linking billing, the above billable resources, public web ingress, and the narrowly scoped IAM configuration below. `provision-gcp.sh` never links a billing account or changes IAM. It refuses to run without an explicit operator flag and enabled project billing:

```bash
BILLING_APPROVED=true bash deploy/provision-gcp.sh
```

Run this only after approval. It enables Compute Engine and creates the reviewed VM/network/firewall/address resources. Existing resources are never deleted. If provisioning partially fails, inspect existing resources against the script before retrying; the script does not reconcile an existing resource's settings. An existing target VM causes an immediate stop. Read startup logs and confirm Docker/Compose installation before deployment. The script installs Docker from Ubuntu packages; it never builds the Java image on the VM.

Project-owner or equivalent provisioning permissions are needed for Compute Engine resources and service enablement. The caller also needs access to the linked billing account. Keep provisioning permissions separate from CI deployment permissions.

## GitLab identity and protected variables

Set up Google Workload Identity Federation for issuer `https://gitlab.com`. Use a dedicated service account for deployment, with no JSON key. Map `google.subject=assertion.sub` and `attribute.project_id=assertion.project_id`. Restrict the provider condition to this immutable GitLab project ID (`87224439`), branch `main`, branch ref type, and `ref_protected == 'true'`. Match the provider's allowed audience to `https://iam.googleapis.com/<provider-resource-name>`, which is the audience in `.gitlab-ci.yml`. Grant `roles/iam.workloadIdentityUser` on the dedicated deploy service account only to that restricted principal set.

Grant the deploy identity `roles/compute.osAdminLogin` on the single VM, `roles/iap.tunnelResourceAccessor` scoped to that VM and SSH port 22, and read permissions needed by `gcloud` to locate the VM/project (`compute.instances.get`, `compute.instances.list`, `compute.projects.get`). A small custom read role avoids granting instance administration. OS Admin Login permits sudo on this dedicated deployment VM; protected branch/pipeline access therefore controls application-host administration. Because the VM has no attached service account, the deployer does not need permission to impersonate a VM runtime service account. Enable the IAP, IAM Credentials, STS, and OS Login APIs as needed during approved setup. Do not grant project Owner/Editor to CI.

See [Google's GitLab federation guide](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines) and [IAP TCP forwarding](https://docs.cloud.google.com/iap/docs/using-tcp-forwarding). IAM setup is intentionally not automated by the provisioning script; permissions must be reviewed before applying them.

Configure these GitLab variables as **protected**, scoped to the production environment where appropriate:

| Variable | Value |
| --- | --- |
| `DEPLOY_ENABLED` | `true` only after approved setup and verification |
| `GCP_PROJECT_ID` | `music-companion-513717` |
| `GCP_ZONE` | `us-central1-a` |
| `GCP_INSTANCE` | `music-companion-demo` |
| `GCP_WIF_PROVIDER` | `projects/<number>/locations/global/workloadIdentityPools/<pool>/providers/<provider>` |
| `GCP_DEPLOY_SERVICE_ACCOUNT` | Dedicated deploy account email |
| `PUBLIC_HOST` | Actual reserved-IP hostname, without scheme or slash |
| `ACME_EMAIL` | Owner-approved certificate renewal contact |
| `GCP_SSH_KNOWN_HOSTS` | **File variable** containing the independently verified VM SSH host public keys |

GitLab supplies `GCP_ID_TOKEN`, `CI_REGISTRY_IMAGE`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD`, `CI_COMMIT_SHA`, and `CI_JOB_ID` for the job. Do not replace these with a persistent personal token. Mask any secret variables; the variables above are mostly identifiers or public keys, not secrets.

For SSH pinning, obtain the numeric instance ID through the authenticated Compute API and inspect `/etc/ssh/ssh_host_ed25519_key.pub` from an independently verified Console/administrator connection. Construct the known-hosts entry as `compute.<numeric-instance-id> ssh-ed25519 <public-key>`. Verify its fingerprint before setting the file variable. Do not use an unverified `ssh-keyscan` result. `ci-deploy.sh` requires strict host verification, creates a temporary SSH key with one-hour expiry, uses IAP, exchanges the GitLab token through WIF, and removes local credential files at job exit. Replacing the VM requires updating the verified host-key entry.

## Release and persistent data

CI builds amd64 images tagged with the full commit SHA at `$CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA` and `/frontend:$CI_COMMIT_SHA`. Only a protected default-branch pipeline with passing tests/security/build jobs and `DEPLOY_ENABLED=true` calls `deploy/ci-deploy.sh`. Neither an MR pipeline nor the GitHub mirror deploys.

The CI script copies only the reviewed Compose/Caddy/release assets to the VM. It passes the temporary registry credential through SSH stdin. The VM stores registry login only in a private temporary Docker configuration, which is removed on exit. `release.sh` serializes deployments with `flock`, pulls images before stopping the old backend, waits for active work to stop, archives the entire data directory, then starts the new commit. Image tags must not be overwritten; protect release tags/registry access. The record includes the commit SHA; `docker inspect` can capture resolved image digests for evidence.

SQLite, original uploads, and the generated Django secret stay in `/srv/music-companion/data`, outside all containers. The backend entrypoint applies migrations and collects static files. PDF rendering and OMR use temporary workspaces; recognized regions remain in SQLite and the original PDF is retained. Caddy's certificate data/configuration persists in sibling directories. Bind mounts survive container replacement and VM stop/start. Disk retention protects against automatic deletion with a VM; it does not make the data immune to deliberate deletion or disk failure.

Only Caddy publishes ports. It sends `/api/` directly to Django with a replaced HTTPS forwarding header; `/admin` and `/media` are denied. Uploaded files are accessed through authorized API routes. Nginx serves the frontend and static assets, without a public port. Django runs with production mode, session ownership, secure cookies, exact allowed host/CSRF origin, and no cross-origin API access. Production session libraries are private to their browser session; this is not Google account login or cross-device recovery.

Container memory/process limits and rotating Docker logs bound routine usage. The backend has 2,304 MiB memory, a 1 GiB Java heap, and a 512 MiB memory-backed `/tmp` workspace; scratch space counts against the container memory limit and disappears on replacement. Very large recognition jobs may exhaust these limits and must return a failure/retry state rather than consume the disk indefinitely. One host is appropriate for the small course demo; avoid simultaneous large recognition requests. Follow the backend's configured upload, page, and recognition limits.

Monitor free disk space: backups are intentionally retained and never silently deleted. Before stopping the service, the release script refuses a new backup if its estimated size would exceed the 2 GiB backup budget or leave less than 1 GiB free. Export/review existing backups with operator approval before retrying; data and previous backups remain intact. Arrange approved retention/export if running beyond the course demonstration. A same-disk backup helps rollback but does **not** protect against loss of the VM disk.

## Verification, recovery, and teardown

The release script checks Compose health, a real public TLS certificate, the frontend, and API status before updating `/srv/music-companion/current-release`. It leaves `pending-release` on failure, retains the previous release record and data archive, and does not claim the PDF workflow passed. Capture the actual pipeline URL and these additional results:

1. Fresh browser: create a private session, upload a permitted PDF, extract measures, open an actual measure preview, navigate with arrow keys, save and remove a practice record.
2. Second independent browser: first browser's scores, original PDF, measure images, and practice records cannot be listed or accessed by guessed IDs or spoofed headers.
3. Restart the backend, then redeploy the same commit: the first browser still retrieves its PDF, measures, and notes.
4. Delete only the disposable test score and verify its file/records are removed. Preserve existing user data.
5. Verify HTTP redirects to HTTPS, `/admin/` and `/media/` return 404, and cloud firewall rules expose no database/backend port.

If deployment fails, inspect `docker compose --env-file /srv/music-companion/releases/<sha>/release.env -f /srv/music-companion/releases/<sha>/compose.production.yaml logs --tail=100` and the saved `pending-release`. Retry after fixing ordinary startup/configuration errors. No automatic data restore occurs: migrations may have changed schema, and new user writes must not be overwritten.

For an application-only rollback, verify the previous code supports the current schema, then deploy the prior approved commit through the same pipeline. For a schema rollback, first stop writers and make another backup; review migration reversibility and choose a matching database/media archive. Restoring an archive can discard newer user changes, so it requires explicit approval. Never run `docker compose down -v`, delete `/srv/music-companion/data`, or remove disks as routine recovery.

Stopping, deleting, or releasing infrastructure requires the owner's instruction. VM deletion protection and retained boot disk must not be disabled without approval. Retaining a reserved IP preserves the DNS hostname but continues IP charges while the VM is stopped. Cost cleanup must consider the VM, retained disk, address, backups, and registry images separately.
