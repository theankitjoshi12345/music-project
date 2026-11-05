#!/usr/bin/env bash
# Deliberately not called by CI. Requires explicit operator billing approval.
set -euo pipefail

if [[ ${BILLING_APPROVED:-false} != true ]]; then
  printf '%s\n' 'STOP: obtain approval for the resources and cost in deploy/README.md, then set BILLING_APPROVED=true.' >&2
  exit 2
fi

readonly project=music-companion-513717
readonly region=us-central1
readonly zone=us-central1-a
readonly vm=music-companion-demo
readonly network=music-companion-demo
readonly subnet=music-companion-demo
readonly address=music-companion-demo
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

billing_enabled=$(gcloud billing projects describe "$project" --format='value(billingEnabled)')
[[ $billing_enabled == True || $billing_enabled == true ]] || {
  printf '%s\n' 'Project billing is disabled. Link an approved billing account separately; this script never links billing.' >&2
  exit 2
}
gcloud services enable compute.googleapis.com --project="$project"

# These dedicated resources are created once. Existing resources are never
# changed or deleted; inspect/reconcile partial provisioning before retrying.
if gcloud compute instances describe "$vm" --zone="$zone" --project="$project" >/dev/null 2>&1; then
  printf '%s\n' 'The target VM already exists. Inspect it; do not create a duplicate.' >&2
  exit 2
fi
if ! gcloud compute networks describe "$network" --project="$project" >/dev/null 2>&1; then
  gcloud compute networks create "$network" --subnet-mode=custom --project="$project"
fi
if ! gcloud compute networks subnets describe "$subnet" --region="$region" --project="$project" >/dev/null 2>&1; then
  gcloud compute networks subnets create "$subnet" --network="$network" --region="$region" --range=10.89.0.0/24 --project="$project"
fi
if ! gcloud compute firewall-rules describe music-companion-web --project="$project" >/dev/null 2>&1; then
  gcloud compute firewall-rules create music-companion-web --network="$network" --allow=tcp:80,tcp:443 --source-ranges=0.0.0.0/0 --target-tags=music-companion-demo --project="$project"
fi
if ! gcloud compute firewall-rules describe music-companion-iap-ssh --project="$project" >/dev/null 2>&1; then
  gcloud compute firewall-rules create music-companion-iap-ssh --network="$network" --allow=tcp:22 --source-ranges=35.235.240.0/20 --target-tags=music-companion-demo --project="$project"
fi
if ! gcloud compute addresses describe "$address" --region="$region" --project="$project" >/dev/null 2>&1; then
  gcloud compute addresses create "$address" --region="$region" --project="$project"
fi
public_ip=$(gcloud compute addresses describe "$address" --region="$region" --project="$project" --format='value(address)')
gcloud compute instances create "$vm" \
  --project="$project" --zone="$zone" --machine-type=e2-medium \
  --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB --boot-disk-type=pd-standard --no-boot-disk-auto-delete \
  --deletion-protection --no-service-account \
  --network="$network" --subnet="$subnet" --address="$public_ip" \
  --tags=music-companion-demo \
  --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
  --metadata=enable-oslogin=TRUE,block-project-ssh-keys=TRUE \
  --metadata-from-file="startup-script=$script_dir/bootstrap-vm.sh" \
  --labels=app=music-companion,environment=course-demo

printf 'VM provisioned. Candidate hostname (NOT yet a verified live URL): music-companion.%s.sslip.io\n' "$public_ip"
printf '%s\n' 'Next: verify bootstrap, approve/configure CI identity, deploy, then test HTTPS and the full PDF workflow.'
