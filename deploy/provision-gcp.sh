#!/usr/bin/env bash
# One-time Google free-tier architecture setup. Never called by CI. The guard
# flags represent the owner's separate approval for billing, APIs/resources,
# IAM changes, and persistent credentials/secrets.
set -euo pipefail
umask 077

for approval in BILLING_APPROVED RESOURCE_DEPLOYMENT_APPROVED IAM_APPROVED; do
  [[ ${!approval:-false} == true ]] || {
    printf 'STOP: %s=true is required after explicit owner approval.\n' "$approval" >&2
    exit 2
  }
done

readonly project=music-companion-513717
readonly region=us-central1
readonly bucket=music-companion-513717-data
readonly repository=music-companion
readonly runtime_account=music-companion-runtime
readonly deploy_account=music-companion-deploy
readonly django_secret=music-companion-django-secret
readonly workload_pool=gitlab
readonly workload_provider=music-companion
readonly gitlab_project_id=87224439

billing_enabled=$(gcloud billing projects describe "$project" --format='value(billingEnabled)')
[[ $billing_enabled == True || $billing_enabled == true ]] || {
  printf '%s\n' 'Project billing is disabled. This script never links a billing account.' >&2
  exit 2
}

gcloud services enable \
  run.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com \
  storage.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com \
  sts.googleapis.com firebase.googleapis.com firebasehosting.googleapis.com \
  --project="$project"

if ! gcloud firestore databases describe --database='(default)' --project="$project" >/dev/null 2>&1; then
  gcloud firestore databases create --database='(default)' --location="$region" \
    --type=datastore-mode --delete-protection --project="$project" --quiet
fi

if ! gcloud storage buckets describe "gs://$bucket" --project="$project" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://$bucket" --project="$project" --location="$region" \
    --uniform-bucket-level-access --public-access-prevention --soft-delete-duration=0s
fi

if ! gcloud artifacts repositories describe "$repository" --location="$region" --project="$project" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$repository" --project="$project" --location="$region" \
    --repository-format=docker --description='Temporary Cloud Run image handoff; CI deletes each deployed image.'
fi

runtime_email="$runtime_account@$project.iam.gserviceaccount.com"
deploy_email="$deploy_account@$project.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "$runtime_email" --project="$project" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$runtime_account" --project="$project" \
    --display-name='Music Companion Cloud Run runtime'
fi
if ! gcloud iam service-accounts describe "$deploy_email" --project="$project" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$deploy_account" --project="$project" \
    --display-name='Music Companion protected GitLab deployer'
fi

gcloud projects add-iam-policy-binding "$project" --member="serviceAccount:$runtime_email" \
  --role=roles/datastore.user --condition=None --quiet
gcloud storage buckets add-iam-policy-binding "gs://$bucket" --member="serviceAccount:$runtime_email" \
  --role=roles/storage.objectUser --quiet

secret_created=false
if ! gcloud secrets describe "$django_secret" --project="$project" >/dev/null 2>&1; then
  gcloud secrets create "$django_secret" --project="$project" --replication-policy=automatic
  secret_created=true
fi
if [[ $secret_created == true ]]; then
  python3 -c 'import secrets; print(secrets.token_urlsafe(64))' | \
    gcloud secrets versions add "$django_secret" --project="$project" --data-file=-
fi
gcloud secrets add-iam-policy-binding "$django_secret" --project="$project" \
  --member="serviceAccount:$runtime_email" --role=roles/secretmanager.secretAccessor --quiet

gcloud projects add-iam-policy-binding "$project" --member="serviceAccount:$deploy_email" \
  --role=roles/run.admin --condition=None --quiet
gcloud projects add-iam-policy-binding "$project" --member="serviceAccount:$deploy_email" \
  --role=roles/firebasehosting.admin --condition=None --quiet
gcloud projects add-iam-policy-binding "$project" --member="serviceAccount:$deploy_email" \
  --role=roles/serviceusage.serviceUsageConsumer --condition=None --quiet
gcloud iam service-accounts add-iam-policy-binding "$runtime_email" --project="$project" \
  --member="serviceAccount:$deploy_email" --role=roles/iam.serviceAccountUser --quiet
gcloud artifacts repositories add-iam-policy-binding "$repository" --project="$project" --location="$region" \
  --member="serviceAccount:$deploy_email" --role=roles/artifactregistry.repoAdmin --quiet
gcloud secrets add-iam-policy-binding "$django_secret" --project="$project" \
  --member="serviceAccount:$deploy_email" --role=roles/secretmanager.viewer --quiet

project_number=$(gcloud projects describe "$project" --format='value(projectNumber)')
if ! gcloud iam workload-identity-pools describe "$workload_pool" --location=global --project="$project" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "$workload_pool" --location=global --project="$project" \
    --display-name='Protected GitLab pipelines'
fi
provider_resource="projects/$project_number/locations/global/workloadIdentityPools/$workload_pool/providers/$workload_provider"
if ! gcloud iam workload-identity-pools providers describe "$workload_provider" \
  --workload-identity-pool="$workload_pool" --location=global --project="$project" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "$workload_provider" \
    --workload-identity-pool="$workload_pool" --location=global --project="$project" \
    --display-name='Music Companion protected main' \
    --issuer-uri=https://gitlab.com \
    --allowed-audiences="https://iam.googleapis.com/$provider_resource" \
    --attribute-mapping='google.subject=assertion.sub,attribute.project_id=assertion.project_id,attribute.ref=assertion.ref,attribute.ref_type=assertion.ref_type,attribute.ref_protected=assertion.ref_protected' \
    --attribute-condition="assertion.project_id=='$gitlab_project_id' && assertion.ref=='main' && assertion.ref_type=='branch' && assertion.ref_protected=='true'"
fi
principal="principalSet://iam.googleapis.com/projects/$project_number/locations/global/workloadIdentityPools/$workload_pool/attribute.project_id/$gitlab_project_id"
gcloud iam service-accounts add-iam-policy-binding "$deploy_email" --project="$project" \
  --member="$principal" --role=roles/iam.workloadIdentityUser --quiet

printf '%s\n' 'Approved Google resources and narrowly scoped identities are configured.'
printf 'GCP_WIF_PROVIDER=%s\n' "$provider_resource"
printf 'GCP_DEPLOY_SERVICE_ACCOUNT=%s\n' "$deploy_email"
printf 'GCP_RUNTIME_SERVICE_ACCOUNT=%s\n' "$runtime_email"
printf 'GCP_STORAGE_BUCKET=%s\n' "$bucket"
printf 'GCP_ARTIFACT_REPOSITORY=%s\n' "$repository"
printf 'GCP_DJANGO_SECRET=%s\n' "$django_secret"
printf '%s\n' 'No Cloud Run service was deployed. Configure protected GitLab variables and approve deployment separately.'
